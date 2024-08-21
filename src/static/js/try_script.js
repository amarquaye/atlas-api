document.getElementById('submit-btn').addEventListener('click', async () => {
    const llmQuery = document.getElementById('llm-query').value;
    const llmResponse = document.getElementById('llm-response').value;

    try {
        const res = await fetch(`https://atlasproject-brown.vercel.app/verify?llm_query=${encodeURIComponent(llmQuery)}&llm_response=${encodeURIComponent(llmResponse)}`);
        const data = await res.json();

        document.getElementById('response-text').textContent = data.response.replace(/\n/g, ' ');
        document.getElementById('source-text').textContent = data.source.replace(/\n/g, ' ');

        document.getElementById('copy-btn').addEventListener('click', () => {
            navigator.clipboard.writeText(JSON.stringify(data, null, 2));
            alert('Result copied to clipboard!');
        });
    } catch (error) {
        alert('Error: ' + error.message);
    }
});