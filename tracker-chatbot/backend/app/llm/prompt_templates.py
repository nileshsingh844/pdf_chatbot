# RAG Prompt Templates for PDF Chatbot

# System prompt for general technical assistance
SYSTEM_PROMPT = """You are a technical assistant specializing in device specifications and documentation. Your role is to help users understand technical documents by providing accurate, concise answers based solely on the provided context.

Guidelines:
- Answer ONLY using information from the provided context
- If information is not available, state "I cannot find this information in the provided document"
- Include page citations in the format (Page X) when referencing specific information
- Be accurate and factual
- Focus on technical specifications and procedures
- Keep responses concise but complete"""

# RAG prompt template
RAG_PROMPT_TEMPLATE = """Context from document:
{context}

User Question: {question}

Based on the provided context, please answer the user's question. Remember to:
1. Use only information from the context
2. Include page citations like (Page X) when referencing specific information
3. State if information is not available
4. Be concise and accurate

Answer:"""

# Follow-up question prompt
FOLLOWUP_PROMPT_TEMPLATE = """Previous conversation context:
{chat_history}

Current document context:
{context}

New question: {question}

Please answer the new question considering both the conversation history and the current document context. Follow the same guidelines for citations and accuracy.

Answer:"""

# Citations extraction prompt
CITATION_PROMPT = """Please review the following answer and ensure all factual statements have proper page citations from the provided context.

Answer: {answer}

Context: {context}

Please rewrite the answer with proper citations in the format (Page X) for all specific information referenced.

Corrected answer:"""

# Summary prompt
SUMMARY_PROMPT_TEMPLATE = """Based on the following document content, provide a concise summary highlighting the key technical specifications and important information.

Document content:
{context}

Please provide a structured summary covering:
1. Main purpose/function
2. Key specifications
3. Important procedures or commands
4. Critical requirements

Summary:"""

# Comparison prompt
COMPARISON_PROMPT_TEMPLATE = """Compare the following information from different pages/sections of the document:

Context 1: {context1}
Context 2: {context2}

User question: {question}

Please provide a comparison highlighting similarities, differences, and any important relationships between the information. Include citations for both sources.

Comparison:"""

# Error handling prompt
ERROR_FALLBACK_PROMPT = """I apologize, but I encountered an error while processing your request. This could be due to:

1. The document might not contain the information you're looking for
2. There might be a technical issue with the search system
3. The question might be unclear

Could you please:
- Rephrase your question
- Check if the information exists in the uploaded document
- Try a more specific search term

If you continue to experience issues, please try uploading the document again or contact support."""

# Welcome message
WELCOME_MESSAGE = """Welcome to the PDF Chatbot! I can help you:

📄 **Upload PDFs** - Drag and drop technical documents
❓ **Ask Questions** - Get answers with page citations
🔍 **Search** - Find specific information quickly
📊 **Export** - Download conversations as markdown

**Example questions you can ask:**
- "What are the power requirements?"
- "How do I configure the GPS module?"
- "What are the voltage specifications?"
- "Show me the communication protocols"

Upload a PDF document to get started!"""

# Help message
HELP_MESSAGE = """**How to use this PDF Chatbot:**

1. **Upload a PDF**: Click the upload area or drag & drop a PDF file (max 100MB)

2. **Ask questions**: Type your question in the chat and press Enter

3. **Get answers**: Receive responses with page citations like (Page 5)

4. **Follow up**: Ask additional questions based on the context

**Tips for better results:**
- Be specific in your questions
- Use technical terms from the document
- Ask about specifications, procedures, or commands
- Reference page numbers if you know them

**Features:**
- 🎯 Hybrid search (vector + keyword)
- 📄 Page citations
- 🌙 Dark/light theme
- 📱 Mobile responsive
- 💾 Export conversations

**Supported file types:**
- PDF documents with text content
- Technical manuals and specifications
- User guides and documentation

Need help? Ask me anything about your uploaded document!"""
