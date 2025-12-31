#!/usr/bin/env node
/**
 * Valley Snow Load Calculator - Automated Backup Scheduler
 * Zips the project folder every hour and uploads to Google Drive
 *
 * Setup Instructions:
 * 1. Enable Google Drive API: https://console.developers.google.com/
 * 2. Create credentials.json in the project root
 * 3. Run: npm install
 * 4. First run will prompt for Google authentication
 *
 * Usage:
 *   node backup-scheduler.js              # Run continuously
 *   node backup-scheduler.js --once       # Run once and exit
 *   node backup-scheduler.js --test       # Test backup creation
 *   npm run backup                        # Via npm script
 */

const fs = require('fs');
const path = require('path');
const archiver = require('archiver');
const cron = require('node-cron');
const { google } = require('googleapis');
const { authenticate } = require('@google-cloud/local-auth');
const os = require('os');

class BackupScheduler {
    constructor(options = {}) {
        this.projectDir = options.projectDir || path.join(__dirname, '..', '..', '..');
        this.backupDir = options.backupDir || path.join(os.homedir(), 'backups', 'valley_snow_calc');
        this.maxBackups = options.maxBackups || 24;
        this.backupCount = 0;

        // Google Drive setup
        this.drive = null;
        this.driveFolderId = null;

        // Ensure backup directory exists
        if (!fs.existsSync(this.backupDir)) {
            fs.mkdirSync(this.backupDir, { recursive: true });
        }

        // Load configuration
        this.config = this.loadConfig();

        console.log('🚀 Backup Scheduler initialized');
        console.log(`📁 Project directory: ${this.projectDir}`);
        console.log(`💾 Backup directory: ${this.backupDir}`);
        console.log(`☁️  Cloud upload: ${this.config.cloudUpload ? 'Enabled' : 'Disabled'}`);
    }

    loadConfig() {
        const configPath = path.join(this.projectDir, 'backup_config.json');
        const defaultConfig = {
            excludePatterns: [
                'node_modules',
                '__pycache__',
                '*.pyc',
                '.git',
                '*.log',
                'auto_backups',
                '*.tmp',
                '.DS_Store',
                'Thumbs.db',
                '*.zip',
                'dist',
                '.next'
            ],
            includeDataFiles: true,
            cloudUpload: true,
            cloudProvider: 'google_drive',
            compressionLevel: 6,
            googleDriveFolder: 'Valley Snow Load Backups'
        };

        if (fs.existsSync(configPath)) {
            try {
                const userConfig = JSON.parse(fs.readFileSync(configPath, 'utf8'));
                Object.assign(defaultConfig, userConfig);
                console.log('✅ Loaded backup configuration from file');
            } catch (error) {
                console.error('❌ Error loading config file:', error.message);
            }
        }

        return defaultConfig;
    }

    async initializeGoogleDrive() {
        try {
            // Check if credentials exist
            const credentialsPath = path.join(this.projectDir, 'credentials.json');
            if (!fs.existsSync(credentialsPath)) {
                console.log('❌ credentials.json not found. Please:');
                console.log('   1. Go to https://console.developers.google.com/');
                console.log('   2. Enable Google Drive API');
                console.log('   3. Create OAuth 2.0 credentials');
                console.log('   4. Download credentials.json to project root');
                return false;
            }

            // Authenticate with Google
            const auth = await authenticate({
                keyfilePath: credentialsPath,
                scopes: ['https://www.googleapis.com/auth/drive.file'],
            });

            this.drive = google.drive({ version: 'v3', auth });

            // Create or find backup folder
            await this.ensureBackupFolder();

            console.log('✅ Google Drive authentication successful');
            return true;

        } catch (error) {
            console.error('❌ Google Drive authentication failed:', error.message);
            console.log('💡 Make sure credentials.json is properly configured');
            return false;
        }
    }

    async ensureBackupFolder() {
        try {
            // Check if folder already exists
            const response = await this.drive.files.list({
                q: `name='${this.config.googleDriveFolder}' and mimeType='application/vnd.google-apps.folder' and trashed=false`,
                fields: 'files(id, name)',
            });

            if (response.data.files.length > 0) {
                this.driveFolderId = response.data.files[0].id;
                console.log(`📁 Using existing Google Drive folder: ${this.config.googleDriveFolder}`);
            } else {
                // Create new folder
                const folderMetadata = {
                    name: this.config.googleDriveFolder,
                    mimeType: 'application/vnd.google-apps.folder',
                };

                const folder = await this.drive.files.create({
                    resource: folderMetadata,
                    fields: 'id',
                });

                this.driveFolderId = folder.data.id;
                console.log(`📁 Created Google Drive folder: ${this.config.googleDriveFolder}`);
            }
        } catch (error) {
            console.error('❌ Failed to create/find Google Drive folder:', error.message);
        }
    }

    async createBackupZip() {
        return new Promise((resolve, reject) => {
            try {
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
                const zipFilename = `valley_snow_calc_backup_${timestamp}.zip`;
                const zipPath = path.join(this.backupDir, zipFilename);

                console.log(`📦 Creating backup: ${zipFilename}`);

                const output = fs.createWriteStream(zipPath);
                const archive = archiver('zip', {
                    zlib: { level: this.config.compressionLevel }
                });

                output.on('close', async () => {
                    const zipSize = fs.statSync(zipPath).size;
                    console.log(`✅ Backup created: ${zipSize} bytes`);

                    this.backupCount++;

                    // Cleanup old backups
                    await this.cleanupOldBackups();

                    // Upload to cloud if enabled
                    if (this.config.cloudUpload && this.drive) {
                        await this.uploadToGoogleDrive(zipPath);
                    }

                    resolve(zipPath);
                });

                archive.on('error', (err) => {
                    console.error('❌ Archive error:', err);
                    reject(err);
                });

                archive.pipe(output);

                // Add files to archive
                this.addFilesToArchive(archive);

                archive.finalize();

            } catch (error) {
                console.error('❌ Failed to create backup:', error);
                reject(error);
            }
        });
    }

    addFilesToArchive(archive) {
        const walkDir = (dir, relativePath = '') => {
            const items = fs.readdirSync(dir);

            for (const item of items) {
                const fullPath = path.join(dir, item);
                const relPath = path.join(relativePath, item);

                // Skip excluded files/directories
                if (this.shouldExclude(item)) {
                    continue;
                }

                const stat = fs.statSync(fullPath);

                if (stat.isDirectory()) {
                    walkDir(fullPath, relPath);
                } else {
                    archive.file(fullPath, { name: relPath });
                }
            }
        };

        walkDir(this.projectDir);
    }

    shouldExclude(name) {
        const excludePatterns = this.config.excludePatterns;

        for (const pattern of excludePatterns) {
            if (pattern.startsWith('*')) {
                if (name.endsWith(pattern.slice(1))) {
                    return true;
                }
            } else if (name.includes(pattern)) {
                return true;
            }
        }

        return false;
    }

    async cleanupOldBackups() {
        try {
            const backupFiles = fs.readdirSync(this.backupDir)
                .filter(file => file.startsWith('valley_snow_calc_backup_') && file.endsWith('.zip'))
                .map(file => ({
                    name: file,
                    path: path.join(this.backupDir, file),
                    mtime: fs.statSync(path.join(this.backupDir, file)).mtime
                }))
                .sort((a, b) => b.mtime - a.mtime);

            if (backupFiles.length > this.maxBackups) {
                const filesToDelete = backupFiles.slice(this.maxBackups);
                for (const file of filesToDelete) {
                    fs.unlinkSync(file.path);
                    console.log(`🧹 Cleaned up old backup: ${file.name}`);
                }
            }
        } catch (error) {
            console.error('❌ Failed to cleanup old backups:', error);
        }
    }

    async uploadToGoogleDrive(zipPath) {
        try {
            if (!this.drive || !this.driveFolderId) {
                console.log('⚠️  Google Drive not initialized, skipping upload');
                return;
            }

            const fileMetadata = {
                name: path.basename(zipPath),
                parents: [this.driveFolderId]
            };

            const media = {
                mimeType: 'application/zip',
                body: fs.createReadStream(zipPath)
            };

            const response = await this.drive.files.create({
                resource: fileMetadata,
                media: media,
                fields: 'id,name'
            });

            console.log(`☁️  Uploaded to Google Drive: ${response.data.name}`);
            console.log(`🔗 File ID: ${response.data.id}`);

        } catch (error) {
            console.error('❌ Google Drive upload failed:', error.message);
        }
    }

    async runOnce() {
        console.log('🔄 Running single backup...');

        // Initialize Google Drive if needed
        if (this.config.cloudUpload) {
            await this.initializeGoogleDrive();
        }

        try {
            const result = await this.createBackupZip();
            console.log(`✅ Backup completed: ${path.basename(result)}`);
            return result;
        } catch (error) {
            console.error('❌ Backup failed:', error);
            return null;
        }
    }

    async runScheduler() {
        console.log('⏰ Starting backup scheduler...');

        // Initialize Google Drive if needed
        if (this.config.cloudUpload) {
            const driveReady = await this.initializeGoogleDrive();
            if (!driveReady) {
                console.log('⚠️  Continuing with local backups only');
            }
        }

        // Run immediately
        await this.runOnce();

        // Schedule hourly backups (cron format: "0 * * * *" = every hour at minute 0)
        cron.schedule('0 * * * *', async () => {
            console.log('⏰ Hourly backup triggered');
            await this.runOnce();
        });

        console.log('✅ Backup scheduler running. Backups will occur every hour.');
        console.log('💡 Press Ctrl+C to stop.');

        // Keep the process running
        process.on('SIGINT', () => {
            console.log('\n🛑 Backup scheduler stopped by user');
            process.exit(0);
        });

        process.on('SIGTERM', () => {
            console.log('\n🛑 Backup scheduler stopped');
            process.exit(0);
        });

        // Keep alive
        setInterval(() => {
            // Ping to keep alive
        }, 60000);
    }

    async testBackup() {
        console.log('🧪 Testing backup creation...');

        // Initialize Google Drive if needed
        if (this.config.cloudUpload) {
            await this.initializeGoogleDrive();
        }

        try {
            const result = await this.createBackupZip();
            if (result) {
                const stats = fs.statSync(result);
                console.log(`✅ Test backup created: ${path.basename(result)}`);
                console.log(`📁 Location: ${path.dirname(result)}`);
                console.log(`📊 Size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);
                console.log(`🕒 Modified: ${stats.mtime.toISOString()}`);
                return result;
            } else {
                console.log('❌ Test backup failed');
                return null;
            }
        } catch (error) {
            console.error('❌ Test backup error:', error);
            return null;
        }
    }
}

// CLI interface
async function main() {
    const args = process.argv.slice(2);
    const options = {};

    // Parse arguments
    if (args.includes('--project-dir') && args.indexOf('--project-dir') + 1 < args.length) {
        options.projectDir = args[args.indexOf('--project-dir') + 1];
    }
    if (args.includes('--backup-dir') && args.indexOf('--backup-dir') + 1 < args.length) {
        options.backupDir = args[args.indexOf('--backup-dir') + 1];
    }
    if (args.includes('--max-backups') && args.indexOf('--max-backups') + 1 < args.length) {
        options.maxBackups = parseInt(args[args.indexOf('--max-backups') + 1]);
    }

    const scheduler = new BackupScheduler(options);

    if (args.includes('--test')) {
        await scheduler.testBackup();
    } else if (args.includes('--once')) {
        await scheduler.runOnce();
    } else {
        await scheduler.runScheduler();
    }
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = BackupScheduler;
