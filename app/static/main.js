window.addEventListener("DOMContentLoaded", () => {
  let currentPredictionId = null;
  // Load versions
  fetch("/version")
    .then((res) => res.json())
    .then((data) => {
      document.getElementById("app_version").textContent = data.app_version;
    })
    .catch((err) => {
      console.error("Error loading app version:", err);
      document.getElementById("app_version").textContent = "Error";
    });


  // Handle form submission
  const form = document.getElementById("sentimentForm");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = document.getElementById("text").value.trim();

    const resultEl = document.getElementById("sentimentResult");
    const feedbackEl = document.getElementById("feedbackSection");

    // Clear previous styles and content on new submission
    resultEl.className = ""; // Remove any previously applied sentiment classes
    resultEl.innerHTML = "";

    if (!text) {
      resultEl.textContent = "Please enter a comment.";
      return;
    }

    const body = new URLSearchParams({ text }).toString();

    try {
      const res = await fetch("/sentiment", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });
      const data = await res.json();
      const { sentiment, prediction_id } = data; // 'confidence' and related data are no longer used here

      currentPredictionId = prediction_id;

      const emoji = sentiment === 1 ? "😊 Positive" : "☹️ Negative";

      resultEl.innerHTML = `<strong>${emoji}</strong>`; // Display only emoji and sentiment text

      // Add color coding based on sentiment
      if (sentiment === 1) {
        resultEl.className = "sentiment-positive";
      } else {
        resultEl.className = "sentiment-negative";
      }

      // Show feedback section
      feedbackEl.style.display = "block";

    } catch (err) {
      console.error("Error fetching sentiment:", err);
      resultEl.textContent = "Error analyzing sentiment.";
    }
  });

  // Handle feedback buttons (no changes needed here, as they are independent of display style)
  document.addEventListener("click", async (e) => {
    if (!currentPredictionId) return;

    if (e.target.classList.contains("feedback-btn")) {
      const feedback = e.target.dataset.feedback;
      await submitFeedback(feedback);
    } else if (e.target.classList.contains("correction-btn")) {
      const correction = e.target.dataset.correction;
      await submitCorrection(correction);
    } else if (e.target.id === "flagBtn") {
      await flagPrediction();
    }
  });

  async function submitFeedback(feedback) {
    try {
      const body = new URLSearchParams({
        prediction_id: currentPredictionId,
        feedback: feedback,
      }).toString();

      await fetch("/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });

      showFeedbackMessage("Thank you for your feedback!");
    } catch (err) {
      console.error("Error submitting feedback:", err);
    }
  }

  async function submitCorrection(correction) {
    try {
      const body = new URLSearchParams({
        prediction_id: currentPredictionId,
        feedback: "incorrect",
        correction: correction,
      }).toString();

      await fetch("/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });

      showFeedbackMessage("Correction recorded. Thank you!");
    } catch (err) {
      console.error("Error submitting correction:", err);
    }
  }

  async function flagPrediction() {
    const reason =
      prompt(
        "Why are you flagging this prediction?\n(inappropriate/wrong_context/other)",
      ) || "other";

    try {
      const body = new URLSearchParams({
        prediction_id: currentPredictionId,
        reason: reason,
      }).toString();

      await fetch("/flag", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });

      showFeedbackMessage("Prediction flagged. Thank you!");
    } catch (err) {
      console.error("Error flagging prediction:", err);
    }
  }

  function showFeedbackMessage(message) {
    const messageEl = document.getElementById("feedbackMessage");
    messageEl.textContent = message;
    messageEl.style.display = "block";
    setTimeout(() => {
      messageEl.style.display = "none";
    }, 3000);
  }
});
