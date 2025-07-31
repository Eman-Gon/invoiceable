# Invoice Processor Frontend

A modern React application for AI-powered invoice processing with real-time chat analysis.

## Features

- **Drag & Drop Upload**: Modern file upload interface with drag-and-drop support
- **Multi-format Support**: Process PDFs, images, and text files  
- **Real-time Processing**: Live progress tracking during document processing
- **Invoice Management**: View, edit, and manage processed invoices
- **Smart Search & Filter**: Find invoices by vendor, amount, date, or status
- **PDF Preview**: Side-by-side view of raw text and structured data
- **GL-ready Export**: Download XLSX/CSV files formatted for accounting systems
- **AI Chat Interface**: Ask questions about your invoices using natural language
- **Session-based Analysis**: Chat sessions automatically created with each batch of processed invoices

## Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Set environment variables:
```bash
# Create .env file
echo "REACT_APP_API_URL=http://localhost:8000" > .env
```

3. Start development server:
```bash
npm start
```

## Configuration

### Environment Variables

- `REACT_APP_API_URL`: Backend API URL (default: http://localhost:8000)

### Chat Session Management

The application automatically creates chat sessions when invoices are processed:
- Each batch of processed invoices creates a new chat session
- Sessions are isolated per user (no cross-user data access)
- Sessions expire after 2 hours of inactivity
- Vector embeddings are generated automatically for semantic search

## Usage

1. **Upload Files**: Drag and drop or click to select invoice files
2. **Process**: Click "Extract Invoice Data" to start processing
3. **Review**: View extracted data in a paginated list
4. **Edit**: Click edit icons to modify extracted fields
5. **Chat**: Use the chat interface to ask questions about your invoices
6. **Export**: Download GL-ready XLSX or CSV files

### Chat Examples

- "What's the total amount across all invoices?"
- "Which vendor charged the most this month?"
- "How many invoices have Net 30 payment terms?"
- "Show me all invoices over $1000"
- "What's the average invoice amount from [vendor name]?"

## GL Export Format

Exported files include these columns for accounting software:
- Date
- Vendor
- Invoice Number  
- Description
- Amount
- Account Code (configurable)
- Payment Terms
- Due Date

## Architecture

- **React 18**: Modern React with hooks and functional components
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API communication
- **react-dropzone**: File upload handling
- **lucide-react**: Modern icon library
- **xlsx**: Excel file generation

## API Integration

The frontend communicates with the FastAPI backend via:

### Document Processing
- `POST /process-document`: Process uploaded files
- `GET /health`: Health check

### Chat Functionality
- `POST /create-session`: Create chat session with invoice data
- `POST /chat`: Send chat messages
- `GET /session/{id}/status`: Check session status
- `DELETE /session/{id}`: Delete session

## Performance

- **Optimized Rendering**: Pagination and virtualization for large datasets
- **Lazy Loading**: Components loaded on demand
- **Caching**: API responses cached where appropriate
- **Session Management**: Automatic cleanup of expired chat sessions

## Browser Support

- Chrome 88+
- Firefox 78+
- Safari 14+
- Edge 88+

## Development

### Build for Production
```bash
npm run build
```

### Analyze Bundle Size
```bash
npm run build
npx serve -s build
```

### Linting
```bash
npm run lint
``` 