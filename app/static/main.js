window.onload = () => {
    fetch('/version/appversion')
        .then(response => response.json())
        .then(data => {
            document.getElementById('app_version').textContent = data.message;
        })
        .catch(err => {
            console.error('Error fetching message:', err);
        });

    fetch('/version/modelversion')
        .then(response => response.json())
        .then(data => {
            document.getElementById('model_version').textContent = data.message;
        })
        .catch(err => {
            console.error('Error fetching message:', err);
        });
};