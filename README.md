# NGO Website with Python Backend

A modern, responsive website for a non-governmental organization with a fully functional Python Flask backend. Features real form processing, database storage, and email notifications.

## ✨ Features

### Frontend
- **Responsive Design**: Modern, mobile-first design with improved styling
- **Interactive Forms**: Contact, donation, and newsletter subscription forms
- **Real-time Feedback**: Loading states, validation, and beautiful alert notifications
- **Smooth Animations**: Hover effects, transitions, and micro-interactions

### Backend (NEW!)
- **Python Flask Backend**: RESTful API endpoints for all forms
- **Database Integration**: SQLAlchemy with SQLite for data persistence
- **Email Notifications**: Automated confirmation emails for form submissions
- **Form Validation**: Server-side validation with proper error handling
- **Admin Dashboard**: Basic statistics endpoint for monitoring

### Pages
- **Home**: Mission highlight with improved hero section
- **About Us**: Mission, vision, objectives, history, and team information
- **Projects**: Current and upcoming projects overview
- **Donate**: Secure donation processing with multiple payment options
- **Contact**: Contact form with regional offices and FAQ

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd testing
   ```

2. **Run the setup script**
   ```bash
   python setup.py
   ```
   This will:
   - Create a virtual environment
   - Install all dependencies
   - Set up the database
   - Create configuration files

3. **Configure email (optional)**
   ```bash
   cp .env.example .env
   # Edit .env with your email settings
   ```

4. **Start the application**
   ```bash
   # Activate virtual environment
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   
   # Run the application
   python app.py
   ```

5. **Open in browser**
   Navigate to `http://localhost:5000`

## 🛠 Tech Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: Database ORM
- **Flask-Mail**: Email functionality
- **SQLite**: Database (easily upgradeable to PostgreSQL/MySQL)

### Frontend
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with custom properties
- **Vanilla JavaScript**: Form handling and API integration
- **Responsive Design**: Mobile-first approach

## 📊 API Endpoints

- `POST /api/contact` - Submit contact form
- `POST /api/donate` - Process donation
- `POST /api/newsletter` - Newsletter subscription
- `GET /api/admin/stats` - Basic statistics

## 🗄 Database Schema

### Contact
- Contact form submissions with status tracking

### Donation  
- Donation records with payment method and project allocation

### Newsletter
- Email subscriptions with status management

## 🎨 Design Improvements

### Modern Styling
- Enhanced color palette with CSS custom properties
- Improved typography with better font choices
- Modern card designs with hover effects
- Better form styling with validation states

### User Experience
- Loading spinners for form submissions
- Beautiful alert notifications with icons
- Smooth transitions and animations
- Better mobile responsiveness

### Form Enhancements
- Real-time validation feedback
- Better error messages
- Loading states with disabled buttons
- Success confirmations

## 📧 Email Configuration

Set up email notifications by configuring these environment variables in `.env`:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@hopefoundation.org
```

## 🚀 Deployment Options

### Local Development
- Run with `python app.py`
- Access at `http://localhost:5000`

### Production Deployment
- **Heroku**: Add Procfile and requirements.txt
- **Railway**: Direct deployment support
- **DigitalOcean App Platform**: One-click deployment
- **VPS**: With gunicorn and nginx

### Static Files (Alternative)
The frontend can still be deployed as static files to:
- GitHub Pages
- Netlify  
- Vercel
- Any static hosting service

## 🧪 Development

### Project Structure
```
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── setup.py           # Setup script
├── .env.example       # Environment configuration template
├── css/
│   └── style.css      # Enhanced styling
├── js/
│   └── main.js        # Frontend JavaScript with API calls
├── *.html             # HTML pages
└── ngo.db            # SQLite database (created automatically)
```

### Adding New Features
1. Add database models in `app.py`
2. Create API endpoints
3. Update frontend forms in HTML
4. Add JavaScript API calls
5. Style with CSS

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues
1. **Port already in use**: Change port in app.py or kill existing process
2. **Email not working**: Check SMTP configuration in .env
3. **Database errors**: Delete ngo.db and restart application
4. **Import errors**: Ensure virtual environment is activated

### Getting Help
- Check the console for error messages
- Verify all dependencies are installed
- Ensure Python version compatibility
- Review configuration in .env file