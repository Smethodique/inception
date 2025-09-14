from flask import Flask, request, jsonify, render_template_string
import logging
from transformers import pipeline
import torch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# HTML template for the web interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Text Summarizer</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #555;
        }
        textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            font-family: inherit;
            resize: vertical;
            min-height: 150px;
            box-sizing: border-box;
        }
        textarea:focus {
            border-color: #667eea;
            outline: none;
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.3);
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            display: block;
            margin: 20px auto;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .result {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            border-left-color: #dc3545;
        }
        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
        }
        .stats {
            margin-top: 15px;
            font-size: 14px;
            color: #666;
            display: flex;
            justify-content: space-between;
        }
        .char-count {
            font-size: 12px;
            color: #999;
            text-align: right;
            margin-top: 5px;
        }
        .info {
            background: #d1ecf1;
            color: #0c5460;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #17a2b8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Text Summarizer</h1>
        
        <div class="info">
            <strong>How to use:</strong> Paste your text below (minimum 50 characters) and click "Summarize" to get an AI-generated summary using the BART model.
        </div>

        <form id="summarizeForm">
            <div class="form-group">
                <label for="text">Enter your text to summarize:</label>
                <textarea 
                    id="text" 
                    name="text" 
                    placeholder="Paste your long text here... (minimum 50 characters required)"
                    required></textarea>
                <div class="char-count" id="charCount">0 characters</div>
            </div>
            
            <button type="submit" class="btn" id="submitBtn">
                📝 Summarize Text
            </button>
        </form>

        <div id="result"></div>
    </div>

    <script>
        const form = document.getElementById('summarizeForm');
        const textArea = document.getElementById('text');
        const submitBtn = document.getElementById('submitBtn');
        const result = document.getElementById('result');
        const charCount = document.getElementById('charCount');

        // Update character count
        textArea.addEventListener('input', function() {
            const count = this.value.length;
            charCount.textContent = count + ' characters';
            
            if (count < 50) {
                charCount.style.color = '#dc3545';
                submitBtn.disabled = true;
            } else {
                charCount.style.color = '#28a745';
                submitBtn.disabled = false;
            }
        });

        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const text = textArea.value.trim();
            if (!text || text.length < 50) {
                showResult('Error: Text must be at least 50 characters long.', 'error');
                return;
            }

            // Show loading state
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Summarizing...';
            showResult('Processing your text with AI... This may take a moment.', 'loading');

            try {
                const response = await fetch('/summarize', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: text })
                });

                const data = await response.json();

                if (response.ok) {
                    showResult(data.summary, 'success', {
                        original: data.original_length,
                        summary: data.summary_length,
                        compression: Math.round((1 - data.summary_length / data.original_length) * 100)
                    });
                } else {
                    showResult('Error: ' + (data.error || 'Unknown error occurred'), 'error');
                }
            } catch (error) {
                showResult('Error: Failed to connect to the summarization service.', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '📝 Summarize Text';
            }
        });

        function showResult(text, type, stats = null) {
            let className = 'result';
            if (type === 'error') className += ' error';
            if (type === 'loading') className += ' loading';

            let html = '<p>' + text + '</p>';
            
            if (stats) {
                html += '<div class="stats">' +
                    '<span>Original: ' + stats.original + ' chars</span>' +
                    '<span>Summary: ' + stats.summary + ' chars</span>' +
                    '<span>Compression: ' + stats.compression + '%</span>' +
                '</div>';
            }

            result.innerHTML = '<div class="' + className + '">' + html + '</div>';
        }
    </script>
</body>
</html>
'''

# Initialize the summarization pipeline
try:
    # Use CPU if CUDA is not available
    device = 0 if torch.cuda.is_available() else -1
    logger.info(f"Using device: {'GPU' if device == 0 else 'CPU'}")
    
    # Initialize the summarization pipeline with facebook/bart-large-cnn
    summarizer = pipeline(
        "summarization",
        model="facebook/bart-large-cnn",
        device=device,
        framework="pt"
    )
    logger.info("Summarization pipeline initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize summarization pipeline: {e}")
    summarizer = None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    status = "healthy" if summarizer is not None else "unhealthy"
    return jsonify({"status": status}), 200 if summarizer else 503

@app.route('/summarize', methods=['GET', 'POST'])
def summarize():
    """Handle both web interface and API requests"""
    if request.method == 'GET':
        # Return the web interface
        return render_template_string(HTML_TEMPLATE)
    
    # Handle POST request (API)
    try:
        # Check if summarizer is available
        if summarizer is None:
            return jsonify({"error": "Summarization service unavailable"}), 503
        
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"error": "Missing 'text' field in request body"}), 400
        
        input_text = data['text']
        
        if not input_text or not input_text.strip():
            return jsonify({"error": "Text field cannot be empty"}), 400
        
        # Validate text length (BART has token limits)
        if len(input_text) < 50:
            return jsonify({"error": "Text too short for summarization (minimum 50 characters)"}), 400
        
        if len(input_text) > 10000:
            # Truncate very long texts
            input_text = input_text[:10000]
            logger.warning("Input text truncated to 10000 characters")
        
        logger.info(f"Summarizing text of length: {len(input_text)}")
        
        # Generate summary
        summary_result = summarizer(
            input_text,
            max_length=150,
            min_length=30,
            do_sample=False,
            truncation=True
        )
        
        summary = summary_result[0]['summary_text']
        
        logger.info(f"Summary generated successfully, length: {len(summary)}")
        
        return jsonify({
            "summary": summary,
            "original_length": len(input_text),
            "summary_length": len(summary)
        })
        
    except Exception as e:
        logger.error(f"Error during summarization: {e}")
        return jsonify({"error": "Internal server error during summarization"}), 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with service information"""
    return jsonify({
        "service": "AI Text Summarizer",
        "model": "facebook/bart-large-cnn",
        "endpoints": {
            "POST /summarize": "Summarize text",
            "GET /health": "Health check"
        },
        "usage": {
            "method": "POST",
            "endpoint": "/summarize",
            "content_type": "application/json",
            "body": {"text": "Your text to summarize here"}
        }
    })

if __name__ == '__main__':
    logger.info("Starting AI Text Summarizer API")
    app.run(host='0.0.0.0', port=5000, debug=False)