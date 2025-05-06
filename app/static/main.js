window.addEventListener('DOMContentLoaded', () => {
    // 1) Load & display the app's version
    fetch('/version')
      .then(res => res.json())
      .then(data => {
        document.getElementById('app_version').textContent = data.app_version;
      })
      .catch(err => {
        console.error('Error loading app version:', err);
        document.getElementById('app_version').textContent = 'Error';
      });
  
    // 2) Load & display the model-service's version
    fetch('/version/modelversion')
      .then(res => res.json())
      .then(data => {
        document.getElementById('model_version').textContent = data.model_service_version;
      })
      .catch(err => {
        console.error('Error loading model version:', err);
        document.getElementById('model_version').textContent = 'Error';
      });
  
    // 3) Wire up the form submit for sentiment
    const form = document.getElementById('sentimentForm');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const ticker = document.getElementById('ticker').value.trim();
      const text = document.getElementById('text').value.trim();
  
      const resultEl = document.getElementById('sentimentResult');
      if (!ticker || !text) {
        resultEl.textContent = 'Please enter both ticker and comment.';
        return;
      }
  
      // Send only the 'text' field to the POST /sentiment endpoint
      const body = new URLSearchParams({ text }).toString();
  
      try {
        const res = await fetch('/sentiment', {
          method: 'POST',
          headers: {'Content-Type': 'application/x-www-form-urlencoded'},
          body
        });
        const { sentiment } = await res.json();
        const emoji = sentiment === 1 ? '😊 Positive' : '☹️ Negative';
        resultEl.textContent = `${emoji} (for ${ticker})`;
      } catch (err) {
        console.error('Error fetching sentiment:', err);
        resultEl.textContent = 'Error analyzing sentiment.';
      }
    });
  });
  