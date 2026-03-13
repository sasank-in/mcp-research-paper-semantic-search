# 📁 File Management Guide

## 🎯 New Features Added

Your AI Assistant now supports advanced file management:

1. **Select Existing Papers** - Choose from pre-loaded research papers
2. **Upload New PDFs** - Add your own research papers
3. **Focus Chat on Specific Papers** - Get targeted responses
4. **Process Uploaded Files** - Add new papers to the searchable database

## 🚀 How to Use

### 1. Access File Management

Click the **"Manage Files"** button in the AI Assistant tab to open the file manager modal.

### 2. View Available Papers

The modal shows all available papers in two categories:
- **Existing** - Pre-loaded research papers (blue badge)
- **Uploaded** - Your uploaded papers (green badge)

### 3. Upload New Papers

**Method 1: Drag & Drop**
- Drag a PDF file into the upload area
- File will upload automatically

**Method 2: Browse**
- Click "Browse Files" button
- Select PDF from your computer
- File uploads immediately

**Requirements:**
- Only PDF files accepted
- Maximum file size: 50MB
- File will be saved to `data/uploads/`

### 4. Process Uploaded Files

After uploading:
1. Click **"Process"** button next to uploaded file
2. System will:
   - Extract text from PDF
   - Split into chunks
   - Generate embeddings
   - Add to searchable database
3. File becomes available for chat context

### 5. Select Papers for Chat

**Option 1: From File Manager**
- Click **"Select"** button next to any paper
- Modal closes and paper is selected

**Option 2: From Chat Interface**
- Use the "Focus on:" dropdown in chat
- Select specific paper or "All papers"

### 6. Chat with Selected Papers

When a paper is selected:
- AI responses will prioritize that paper's content
- Source citations will show which papers were used
- Toggle RAG on/off to control context usage

## 🎨 UI Features

### File Manager Modal
- **Professional Design** - Clean, corporate styling
- **Drag & Drop** - Intuitive file upload
- **Progress Indicators** - Visual upload feedback
- **File Information** - Size, type, status badges
- **Action Buttons** - Select, Process, Clear actions

### Chat Enhancements
- **File Selector** - Dropdown to choose focus paper
- **Source Tags** - Shows which papers were referenced
- **Context Indicators** - Visual feedback when RAG is used
- **Smart Responses** - AI adapts based on selected paper

### Notifications
- **Upload Success** - Confirms file uploaded
- **Processing Status** - Shows when file is being processed
- **Error Messages** - Clear feedback on issues
- **Selection Feedback** - Confirms paper selection

## 📊 File Information Display

Each file shows:
- **📄 File Name** - Original PDF filename
- **⚖️ File Size** - Size in KB
- **🏷️ Type Badge** - Existing vs Uploaded
- **🔧 Actions** - Select, Process buttons

## 🔍 Search Integration

### How It Works
1. **All Papers Mode** - Searches across all processed papers
2. **Selected Paper Mode** - Prioritizes selected paper content
3. **Smart Filtering** - AI focuses on relevant paper sections
4. **Source Attribution** - Shows which papers provided context

### Example Workflow
```
1. Upload "my-research.pdf"
2. Click "Process" to add to database
3. Select "my-research.pdf" from dropdown
4. Ask: "What are the main contributions?"
5. AI responds with content from your paper
6. Source tag shows "my-research.pdf"
```

## 🛠️ Technical Details

### File Storage
- **Existing Papers**: `data/papers/` (pre-loaded)
- **Uploaded Papers**: `data/uploads/` (user uploads)
- **Database**: PostgreSQL with vector embeddings

### Processing Pipeline
1. **PDF Loading** - Extract text using PyPDF
2. **Text Chunking** - Split into 800-character chunks
3. **Embedding Generation** - Create 768-dim vectors
4. **Database Storage** - Store in `paper_chunks` table
5. **Indexing** - Add to vector search index

### API Endpoints
- `GET /api/files` - List available files
- `POST /api/files/upload` - Upload new PDF
- `POST /api/files/process/{filename}` - Process uploaded file
- `POST /api/chat` - Enhanced with file selection

## 💡 Use Cases

### Research Analysis
```
1. Upload your research paper
2. Select it for focused chat
3. Ask: "Summarize the methodology"
4. Get targeted response from your paper
```

### Paper Comparison
```
1. Select "attention-paper.pdf"
2. Ask: "How does this compare to BERT?"
3. AI uses attention paper as primary context
4. Provides focused comparison
```

### Literature Review
```
1. Upload multiple related papers
2. Process all papers
3. Switch between papers using dropdown
4. Ask similar questions to compare approaches
```

### Learning & Understanding
```
1. Select complex paper (e.g., "transformer.pdf")
2. Ask: "Explain this paper simply"
3. Get explanation focused on that specific paper
4. Follow up with detailed questions
```

## 🎯 Best Practices

### For Better Results
1. **Process Before Chatting** - Always process uploaded files first
2. **Use Specific Questions** - Ask about particular sections or concepts
3. **Select Relevant Papers** - Choose papers related to your question
4. **Enable RAG** - Keep context enabled for paper-specific questions

### File Organization
1. **Descriptive Names** - Use clear, descriptive PDF filenames
2. **Relevant Content** - Upload papers related to your research area
3. **Quality PDFs** - Ensure PDFs have extractable text (not just images)
4. **Reasonable Size** - Keep files under 50MB for best performance

## 🐛 Troubleshooting

### Upload Issues
**Problem**: File won't upload
**Solutions**:
- Check file is PDF format
- Ensure file size < 50MB
- Verify internet connection
- Try different browser

### Processing Errors
**Problem**: "Error processing file"
**Solutions**:
- Ensure PDF has extractable text
- Check file isn't corrupted
- Verify database is running
- Try re-uploading file

### Chat Not Using Selected Paper
**Problem**: AI not focusing on selected paper
**Solutions**:
- Ensure RAG is enabled
- Verify paper was processed
- Check paper contains relevant content
- Try more specific questions

### No Files Showing
**Problem**: File list is empty
**Solutions**:
- Check `data/papers/` has PDF files
- Run ingestion: `python main.py ingest`
- Refresh browser page
- Check console for errors

## 🎉 Benefits

### Enhanced Productivity
- **Focused Research** - Get answers from specific papers
- **Quick Upload** - Add new papers instantly
- **Smart Context** - AI understands which paper to reference
- **Source Tracking** - Know exactly where information comes from

### Better Accuracy
- **Targeted Responses** - AI focuses on relevant content
- **Source Attribution** - Clear citation of paper sources
- **Context Control** - Toggle RAG on/off as needed
- **Paper-Specific Insights** - Deep understanding of individual papers

### User Experience
- **Intuitive Interface** - Easy drag-and-drop upload
- **Visual Feedback** - Clear progress and status indicators
- **Professional Design** - Corporate-style UI
- **Responsive Layout** - Works on all devices

## 🚀 What's New Summary

✅ **File Upload** - Drag & drop PDF upload
✅ **File Processing** - Convert PDFs to searchable content
✅ **Paper Selection** - Focus chat on specific papers
✅ **Source Attribution** - See which papers provided context
✅ **File Management** - Professional modal interface
✅ **Smart Context** - AI adapts to selected papers
✅ **Visual Feedback** - Notifications and progress indicators
✅ **Responsive Design** - Works on desktop and mobile

## 🎯 Next Steps

1. **Try It Out** - Upload a research paper
2. **Process It** - Add to searchable database
3. **Select It** - Choose for focused chat
4. **Ask Questions** - Get targeted responses
5. **Explore Features** - Try different papers and questions

---

**Your AI Assistant is now significantly more powerful with file management capabilities!** 🚀

**Access it at: http://localhost:8000**