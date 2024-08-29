document.getElementById('submit-btn').addEventListener('click', async () => {
    const llmQuery = document.getElementById('llm-query').value;
    const llmResponse = document.getElementById('llm-response').value;

    try {
        const res = await fetch(`http://localhost:3000/verify?llm_query=${encodeURIComponent(llmQuery)}&llm_response=${encodeURIComponent(llmResponse)}`);
        const data = await res.json();

        const formattedResponse = data.response.replace(/\n/g, ' ');
        const formattedSource = data.source.replace(/\n/g, ' ');

        document.getElementById('response-text').textContent = formattedResponse;
        document.getElementById('source-text').textContent = formattedSource;

        document.getElementById('copy-btn').addEventListener('click', () => {
            const textToCopy = `Response: ${formattedResponse}\n\nSource: ${formattedSource}`;
            navigator.clipboard.writeText(textToCopy);
            alert('Response copied to clipboard!');
        });
    } catch (error) {
        alert('Error: ' + error.message);
    }
});

const modeToggle = document.getElementById('mode-toggle');
const html = document.documentElement;

modeToggle.addEventListener('click', () => {
    html.classList.toggle('dark-mode');
    modeToggle.textContent = html.classList.contains('dark-mode') ? 'Light Mode' : 'Dark Mode';
})
