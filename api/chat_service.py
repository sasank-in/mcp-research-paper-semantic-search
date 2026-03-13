import os
from groq import Groq
from dotenv import load_dotenv
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from retrieval.query_engine import search_similar_papers

load_dotenv()

class ChatService:
    def __init__(self):
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=api_key)
        self.model = os.getenv('GROQ_MODEL', 'llama-3.1-70b-versatile')
        self.conversation_history = []
    
    def chat_with_context(self, user_message: str, use_rag: bool = True, top_k: int = 3, selected_file: str = None):
        """Chat with AI using RAG context from papers"""
        context = ""
        sources = []
        
        if use_rag:
            # Get relevant context from papers
            if selected_file:
                # Search only in selected file
                results = search_similar_papers(user_message, top_k=top_k)
                # Filter results to only include selected file
                results = [(content, source, similarity) for content, source, similarity in results 
                          if selected_file in source]
            else:
                # Search all papers
                results = search_similar_papers(user_message, top_k=top_k)
            
            if results:
                context_parts = []
                for content, source, similarity in results:
                    filename = source.split('/')[-1] if '/' in source else source.split('\\')[-1] if '\\' in source else source
                    context_parts.append(f"[Source: {filename}]\n{content[:500]}...")
                    if filename not in sources:
                        sources.append(filename)
                
                context = "\n\n".join(context_parts)
        
        # Build system message
        system_message = """You are a helpful AI research assistant. You help users understand research papers and answer questions about AI, machine learning, and deep learning topics.

When provided with context from research papers, use that information to give accurate, detailed answers. Always cite the source when using information from the papers.

Be professional, clear, and concise in your responses."""
        
        # Build messages for API
        messages = [{"role": "system", "content": system_message}]
        
        # Add conversation history
        for msg in self.conversation_history[-6:]:  # Keep last 3 exchanges
            messages.append(msg)
        
        # Add context if available
        if context:
            user_message_with_context = f"""Context from research papers:
{context}

User question: {user_message}

Please answer based on the context provided above, and cite the sources."""
        else:
            user_message_with_context = user_message
        
        messages.append({"role": "user", "content": user_message_with_context})
        
        # Get response from Groq
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stream=False
            )
            
            assistant_message = response.choices[0].message.content
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return {
                "response": assistant_message,
                "model": self.model,
                "context_used": bool(context),
                "sources": sources
            }
        
        except Exception as e:
            raise Exception(f"Error calling Groq API: {str(e)}")
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_history(self):
        """Get conversation history"""
        return self.conversation_history

# Global chat service instance
chat_service = ChatService()
