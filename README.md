# Patte Conservation - Website with Python Backend

A modern, responsive website for Patte Conservation, a marine conservation organization. Features a Python Flask backend API serving financial data, campaign information, and cryptocurrency addresses to a beautiful HTML/CSS/JavaScript frontend.

## ✨ Features

### Frontend
- **Responsive Design**: Modern, mobile-first design with beautiful styling
- **Interactive Forms**: Contact, donation, and newsletter subscription forms with validation
- **Smooth Animations**: Hover effects, transitions, and micro-interactions
- **Client-side Validation**: Form validation and user feedback without backend dependency

### Pages
- **Home**: Mission highlight with hero section  
- **About Us**: Mission, vision, objectives, history, and team information
- **Projects**: Current and upcoming projects overview
- **Donate**: Donation form with multiple options and validation
- **Contact**: Contact form with organization information
- **Get Involved**: Volunteer opportunities and partnership information
- **Partners**: Partner organizations and collaborations

## 🚀 Quick Start

### Option 1: With Python Backend (Recommended)
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the Flask backend server
python app.py

# Then open http://localhost:8000 in your browser
```

### Option 2: Static Only (Limited functionality)
```bash
# Python 3
python -m http.server 8000

# Python 2
python -m SimpleHTTPServer 8000

# Node.js (if you have it)
npx http-server

# Then open http://localhost:8000 in your browser
```
Note: Financial data and cryptocurrency addresses will not load without the Python backend.

## 🛠 Tech Stack

### Backend
- **Python 3**: Core backend language
- **Flask**: Lightweight web framework
- **Flask-CORS**: Cross-origin resource sharing support

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with custom properties and responsive design
- **Vanilla JavaScript**: Form handling, validation, and API integration

## 🎨 Design Features

- **CSS Custom Properties**: Consistent theming and easy customization
- **Responsive Grid System**: Mobile-first responsive layouts
- **Modern Typography**: Clean, readable fonts with proper hierarchy
- **Accessibility**: Semantic HTML and proper ARIA labels
- **Performance**: Optimized CSS and minimal JavaScript

## 📁 Project Structure
```
├── index.html              # Homepage
├── about.html              # About page
├── projects.html           # Projects page
├── partners.html           # Partners page
├── donate.html            # Donation page
├── contact.html           # Contact page
├── get-involved.html      # Volunteer/partnership page
├── thank-you.html         # Thank you page (for donations)
├── financial.html         # Financial information
├── foto.html             # Photo gallery
├── css/
│   └── style.css         # Main stylesheet
├── js/
│   └── main.js           # JavaScript functionality
├── images/               # Image assets
└── README.md            # This file
```

## 🚀 Deployment Options

### Static Hosting (Recommended)
This website can be deployed to any static hosting service:

- **GitHub Pages**: Free hosting for GitHub repositories
- **Netlify**: Drag-and-drop deployment with CI/CD
- **Vercel**: Fast deployment with preview links
- **Surge.sh**: Simple command-line deployment
- **AWS S3 + CloudFront**: Scalable cloud hosting

### Local Development Server
For development, use any local HTTP server to avoid CORS issues:
```bash
python -m http.server 8000
# or
npx live-server
# or
php -S localhost:8000
```

## 💡 Customization

### Colors and Branding
Edit the CSS custom properties in `css/style.css`:
```css
:root {
    --primary-color: #2c5530;    /* Main brand color */
    --accent-color: #f39c12;     /* Accent/CTA color */
    --text-dark: #2c3e50;        /* Main text color */
    /* ... other variables ... */
}
```

### Content Updates
- Update text content directly in the HTML files
- Replace images in the `images/` folder
- Modify contact information in `contact.html`
- Update donation amounts and options in `donate.html`

### Form Integration
The forms currently show success messages client-side. To integrate with a backend service:

1. **Contact Form**: Connect to Formspree, Netlify Forms, or similar service
2. **Newsletter**: Integrate with Mailchimp, ConvertKit, or similar
3. **Donations**: Integrate with Stripe, PayPal, or donation platform

## 🌍 Browser Compatibility

- ✅ Chrome (90+)
- ✅ Firefox (85+)
- ✅ Safari (14+)
- ✅ Edge (90+)
- ⚠️ Internet Explorer (not supported)

## 📱 Mobile Responsiveness

The website is fully responsive and works well on:
- 📱 Mobile phones (320px+)
- 📱 Tablets (768px+)
- 💻 Laptops (1024px+)
- 🖥️ Desktop computers (1200px+)

## 🤝 Contributing

1. Fork the repository
2. Make your changes
3. Test on multiple devices/browsers
4. Submit a pull request

## 📄 License

MIT License - feel free to use this template for your own conservation organization.

## 🆘 Troubleshooting

### Forms Not Working
- Ensure you're running via HTTP server (not file://)
- Check browser console for JavaScript errors
- Verify form input names match JavaScript expectations

### Styling Issues
- Clear browser cache
- Check CSS file path in HTML
- Ensure images exist in the images/ folder

### Mobile Display Problems
- Test viewport meta tag is present
- Check CSS media queries
- Ensure touch targets are large enough (44px minimum)

---

**Patte Conservation** - Protecting marine ecosystems and supporting coastal communities in Kenya.