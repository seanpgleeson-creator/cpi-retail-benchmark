# CPI Retail Benchmark Platform - Frontend

## Overview

This is the web dashboard for the CPI Retail Benchmark Platform, providing an intuitive interface for:

- **Dashboard Overview** - Real-time status of all platform services
- **Price Comparison** - Compare retail prices with BLS Consumer Price Index data
- **Retail Scraping** - Scrape current prices from retail websites
- **API Documentation** - Interactive API testing and documentation

## Features

### 🎛️ Dashboard
- Service health monitoring (BLS, Storage, Scrapers, Processing)
- Quick actions for common tasks
- Recent activity tracking
- Real-time status updates

### ⚖️ Price Comparison
- Select product categories (milk, bread, eggs, etc.)
- Choose retailers for comparison
- Location-based pricing (ZIP code)
- Interactive charts and data visualization
- BLS vs retailer price analysis

### 🕷️ Retail Scraping
- Search products across retailers
- Category-based scraping
- Real-time scraping progress
- Product cards with detailed information
- Demo functionality for testing

### 📡 API Testing
- Interactive endpoint testing
- Real-time API responses
- Organized by service category
- JSON response formatting

## Technology Stack

- **HTML5** - Semantic markup
- **CSS3** - Modern responsive design with CSS Grid and Flexbox
- **Vanilla JavaScript** - No framework dependencies
- **Chart.js** - Data visualization
- **Font Awesome** - Icons
- **CSS Variables** - Theming and consistency

## Design Principles

### 🎨 Modern UI/UX
- Clean, professional design
- Intuitive navigation
- Responsive layout for all devices
- Consistent color scheme and typography

### 📱 Mobile-First
- Responsive design that works on all screen sizes
- Touch-friendly interface elements
- Optimized for mobile performance

### ⚡ Performance
- Minimal dependencies
- Efficient DOM manipulation
- Lazy loading of data
- Optimized API calls

### ♿ Accessibility
- Semantic HTML structure
- Keyboard navigation support
- Screen reader friendly
- High contrast color scheme

## File Structure

```
frontend/
├── index.html          # Main dashboard HTML
├── styles.css          # Complete CSS styling
├── script.js           # Dashboard JavaScript functionality
└── README.md          # This file
```

## API Integration

The frontend integrates with the following API endpoints:

### BLS Data API
- `/api/v1/bls/health` - Service health
- `/api/v1/bls/series/popular` - Popular series
- `/api/v1/bls/series/{id}/info` - Series information

### Data Processing API
- `/api/v1/processing/health` - Service health
- `/api/v1/processing/calculations/demo` - Demo calculations

### Storage API
- `/api/v1/storage/stats` - Database statistics
- `/api/v1/storage/series/list` - Stored series

### Scraping API
- `/api/v1/scrapers/health` - Scraper health
- `/api/v1/scrapers/categories` - Available categories
- `/api/v1/scrapers/search` - Product search
- `/api/v1/scrapers/demo/milk` - Demo scraping

## Usage

### Development
The frontend is served automatically by the FastAPI application:

1. Start the backend server
2. Navigate to `http://localhost:8000`
3. The dashboard will load automatically

### Production
The frontend is deployed as static files on Vercel alongside the API:

- **Dashboard**: `https://your-app.vercel.app/`
- **API Docs**: `https://your-app.vercel.app/docs`

## Browser Support

- **Chrome** 90+
- **Firefox** 88+
- **Safari** 14+
- **Edge** 90+

## Features in Detail

### Dashboard Overview
- Real-time service status monitoring
- Quick action buttons for common tasks
- Activity feed showing recent operations
- Service health indicators

### Price Comparison
- Category selection with auto-populated options
- Multi-retailer selection with checkboxes
- ZIP code input for location-based pricing
- Interactive bar charts showing price comparisons
- Detailed results table with normalized pricing

### Retail Scraping
- Free-text product search
- Category filtering for better results
- Configurable result limits
- Real-time scraping progress indicators
- Product cards showing detailed information

### API Documentation
- Organized endpoint categories
- One-click endpoint testing
- Real-time response display
- JSON formatting and syntax highlighting

## Customization

### Theming
The CSS uses custom properties (CSS variables) for easy theming:

```css
:root {
  --primary-color: #667eea;
  --secondary-color: #764ba2;
  --success-color: #48bb78;
  --warning-color: #ed8936;
  --error-color: #f56565;
}
```

### Configuration
JavaScript configuration can be modified in `script.js`:

```javascript
// API configuration
let apiBaseUrl = window.location.origin;

// Chart configuration
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false
};
```

## Contributing

When adding new features to the frontend:

1. Follow the existing code structure
2. Maintain responsive design principles
3. Add appropriate error handling
4. Update this README if needed
5. Test across different browsers and devices

## Performance Optimization

- **Lazy Loading**: Data is loaded only when sections are accessed
- **Efficient DOM**: Minimal DOM manipulation and reuse of elements
- **Caching**: API responses are cached where appropriate
- **Compression**: CSS and JS are minified in production

## Security Considerations

- **CORS**: Proper CORS configuration for API access
- **Input Validation**: All user inputs are validated
- **XSS Prevention**: Proper escaping of dynamic content
- **HTTPS**: All API calls use HTTPS in production
