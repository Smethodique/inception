# AI Text Summarizer API - Curl Examples

## Service Information
The AI text summarizer is accessible at: `https://stakhtou.42.fr/summarize`
- **Model**: facebook/bart-large-cnn (state-of-the-art summarization)
- **Method**: POST
- **Content-Type**: application/json

## Basic Usage Examples

### 1. Simple Text Summarization (HTTPS)
```bash
curl -X POST https://stakhtou.42.fr/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of intelligent agents: any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term artificial intelligence is often used to describe machines that mimic cognitive functions that humans associate with the human mind, such as learning and problem solving. As machines become increasingly capable, tasks considered to require intelligence are often removed from the definition of AI, a phenomenon known as the AI effect. A quip in Teslers Theorem says that AI is whatever hasnt been done yet. For instance, optical character recognition is frequently excluded from things considered to be AI, having become a routine technology."
  }'
```

### 2. HTTP Version (bypasses SSL redirect)
```bash
curl -X POST http://localhost/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The COVID-19 pandemic has fundamentally changed how we work, learn, and interact. Remote work became the norm for millions of people worldwide, leading to a surge in demand for video conferencing tools, cloud computing services, and digital collaboration platforms. Educational institutions rapidly shifted to online learning, forcing both teachers and students to adapt to new technologies and teaching methods. The healthcare industry accelerated its adoption of telemedicine, allowing patients to receive care without visiting hospitals or clinics in person. Supply chains were disrupted globally, highlighting the importance of local production and diversified sourcing strategies. Small businesses faced unprecedented challenges, with many forced to close temporarily or permanently, while others pivoted to digital sales channels and delivery services."
  }'
```

### 3. News Article Summarization
```bash
curl -X POST https://stakhtou.42.fr/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Scientists at the European Space Agency announced today a groundbreaking discovery in the search for extraterrestrial life. The James Webb Space Telescope has detected water vapor and methane in the atmosphere of exoplanet K2-18b, located 120 light-years away in the constellation Leo. The planet, which is 2.6 times the radius of Earth, lies within the habitable zone of its host star, where temperatures could allow liquid water to exist. This marks the first time that both water vapor and methane have been detected simultaneously in the atmosphere of an exoplanet in the habitable zone. The discovery was made using the telescopes advanced infrared instruments, which can analyze the chemical composition of distant atmospheres by studying how starlight passes through them. While the presence of these molecules doesnt confirm the existence of life, it represents a significant step forward in our understanding of potentially habitable worlds beyond our solar system."
  }'
```

### 4. Technical Documentation Summary
```bash
curl -X POST https://stakhtou.42.fr/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Docker is a platform that uses OS-level virtualization to deliver software in packages called containers. Containers are isolated from one another and bundle their own software, libraries and configuration files; they can communicate with each other through well-defined channels. Because all of the containers share the services of a single operating system kernel, they use fewer resources than virtual machines. Docker can package an application and its dependencies in a virtual container that can run on any Linux, Windows, or macOS computer. This enables the application to run in a variety of locations, such as on-premises, in public or private cloud. Docker uses a client-server architecture. The Docker client talks to the Docker daemon, which does the heavy lifting of building, running, and distributing your Docker containers. The Docker client and daemon can run on the same system, or you can connect a Docker client to a remote Docker daemon."
  }'
```

### 5. Check Service Health
```bash
curl -X GET https://stakhtou.42.fr/summarize \
  -H "Content-Type: application/json"
```

### 6. Get Service Information
```bash
curl -X GET https://stakhtou.42.fr/summarize/ \
  -H "Content-Type: application/json"
```

## Expected Response Format

Successful summarization returns:
```json
{
  "summary": "Condensed version of your input text...",
  "original_length": 1250,
  "summary_length": 87
}
```

## Error Responses

### Text Too Short (< 50 characters)
```json
{
  "error": "Text too short for summarization (minimum 50 characters)"
}
```

### Missing Text Field
```json
{
  "error": "Missing 'text' field in request body"
}
```

### Service Unavailable
```json
{
  "error": "Summarization service unavailable"
}
```

## Advanced Examples

### 7. Scientific Paper Abstract
```bash
curl -X POST https://stakhtou.42.fr/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Machine learning has emerged as a powerful tool for analyzing complex datasets in various scientific domains. In this study, we present a novel deep learning architecture for predicting protein folding patterns from amino acid sequences. Our approach combines convolutional neural networks (CNNs) with long short-term memory (LSTM) networks to capture both local and global sequence features. We trained our model on a dataset of 50,000 known protein structures from the Protein Data Bank (PDB) and achieved an accuracy of 92.3% on a held-out test set. The model demonstrates superior performance compared to existing methods, with a 15% improvement in prediction accuracy and 40% reduction in computational time. Furthermore, we validated our predictions using experimental data from X-ray crystallography and nuclear magnetic resonance (NMR) spectroscopy. The results suggest that our method could significantly accelerate protein structure prediction and drug discovery processes."
  }'
```

### 8. Business Report Summary
```bash
curl -X POST https://stakhtou.42.fr/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The quarterly financial report shows strong performance across all business segments. Revenue increased by 18% year-over-year, reaching $2.4 billion, driven primarily by growth in cloud services and software licensing. The cloud division alone contributed $890 million, representing a 35% increase from the previous quarter. Operating expenses were well-controlled, rising only 8% despite significant investments in research and development. Net income reached $420 million, exceeding analyst expectations by 12%. The company maintained a healthy cash flow of $380 million and reduced debt by $150 million. Looking forward, management expects continued growth in the cloud segment, with projected revenue of $1.2 billion for the next quarter. However, they cautioned about potential headwinds from increased competition and regulatory challenges in international markets."
  }'
```

## Tips for Best Results

1. **Text Length**: Optimal range is 200-5000 characters
2. **Language**: Works best with English text
3. **Content Type**: Performs well on:
   - News articles
   - Research papers
   - Business documents
   - Technical documentation
   - Educational content

4. **Avoid**: Very short texts, bullet points, code snippets

## Testing the Service

Run this quick test to verify everything is working:

```bash
# Quick test with a simple example
curl -X POST https://stakhtou.42.fr/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The quick brown fox jumps over the lazy dog. This pangram contains every letter of the English alphabet at least once. It has been used for decades to test typewriters, computer keyboards, and font displays. The phrase is also commonly used in typography and graphic design to showcase different fonts and text layouts. Despite its simplicity, it serves as an effective tool for ensuring that all letters render correctly in various applications and systems."
  }'
```

Expected response should contain a concise summary of the pangram explanation.

## Troubleshooting

- **301 Redirect**: If you get a redirect, the service is working but HTTP is being redirected to HTTPS
- **Connection Refused**: Check if all containers are running with `docker compose ps`
- **Invalid JSON**: Ensure your JSON is properly formatted and escaped
- **Timeout**: Large texts may take 10-30 seconds to process

The AI summarizer is now fully integrated into your Docker infrastructure and accessible through the nginx reverse proxy!