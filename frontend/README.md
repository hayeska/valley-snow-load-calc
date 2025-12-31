# Valley Snow Load Calculator - React Frontend

A modern, responsive React frontend for the Valley Snow Load Calculator built with Vite, TypeScript, Tailwind CSS, and shadcn/ui components.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:5173 in your browser
```

## 🛠️ Tech Stack

- **React 18** - Modern React with hooks and functional components
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Beautiful, accessible component library
- **Radix UI** - Low-level UI primitives

## 📦 Key Features

### 🎨 Modern UI/UX

- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Professional Components**: shadcn/ui provides polished, accessible components
- **Dark/Light Mode Ready**: Tailwind CSS setup supports theme switching
- **Loading States**: Smooth loading indicators during calculations
- **Error Handling**: Clear error messages and user feedback

### 📊 Engineering Calculator

- **Real-time Calculations**: Instant results as you type
- **ASCE 7-22 Compliant**: Based on official snow load standards
- **Comprehensive Results**: Uniform loads, drift loads, and design values
- **Professional Output**: Tabbed interface for different result views

### 🔧 Developer Experience

- **TypeScript**: Full type safety and IntelliSense
- **Hot Reload**: Instant updates during development
- **Component Library**: Reusable, well-documented components
- **Clean Architecture**: Separated concerns and maintainable code

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── ui/           # shadcn/ui components
│   ├── services/         # Calculator API integration
│   ├── types/            # TypeScript type definitions
│   ├── App.tsx           # Main application component
│   ├── main.tsx          # React entry point
│   └── index.css         # Tailwind CSS imports
├── public/               # Static assets
├── package.json          # Dependencies and scripts
├── tailwind.config.js    # Tailwind configuration
├── components.json       # shadcn/ui configuration
└── vite.config.ts        # Vite configuration
```

## 🎯 Component Library

### Core Components Used

- **Card**: Section containers with headers and content
- **Button**: Primary actions with loading states
- **Input/Label**: Form controls with proper accessibility
- **Select**: Dropdown menus for factor selection
- **Tabs**: Organized content sections
- **Table**: Structured data presentation
- **Alert**: Status messages and warnings
- **Separator**: Visual content dividers

### Layout Features

- **Responsive Grid**: Adapts to screen sizes
- **Flexbox Layout**: Clean component alignment
- **Mobile-First**: Optimized for mobile devices
- **Professional Spacing**: Consistent padding and margins

## 🔗 Backend Integration

The frontend integrates with the TypeScript backend library located in `../development_v2/typescript_version/`. The calculator service provides:

- **Roof Geometry Input**: Complete structural parameters
- **Snow Load Calculations**: ASCE 7-22 compliant formulas
- **Result Processing**: Formatted output for display
- **Error Handling**: Graceful failure management

## 🚀 Deployment

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

The built files will be in the `dist/` directory, ready for deployment to any static hosting service.

## 🎨 Customization

### Adding New Components

```bash
# Add new shadcn/ui components
npx shadcn-ui@latest add [component-name]
```

### Theme Customization

- Modify `tailwind.config.js` for color schemes
- Update CSS variables in `src/index.css`
- Customize component variants in component files

### Calculator Integration

- Extend `src/services/calculator.ts` for new calculations
- Add new input fields to the form
- Update result display components

## 📱 Mobile Responsiveness

The application is fully responsive with:

- **Breakpoint System**: sm/md/lg/xl breakpoints
- **Touch-Friendly**: Large touch targets and spacing
- **Readable Text**: Appropriate font sizes across devices
- **Optimized Layout**: Single column on mobile, multi-column on desktop

## 🔧 Development Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
```

## 🤝 Contributing

1. Follow the existing component patterns
2. Use TypeScript for type safety
3. Test on multiple screen sizes
4. Maintain accessibility standards
5. Keep calculations accurate and documented

## 📄 License

Same as the main project - MIT License.
