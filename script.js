$(document).ready(function() {
    $('#submit_query').click(function() {
        const query = $('#customer_query').val();
        if (!query) {
            alert("Please enter a customer query.");
            return;
        }

        $.ajax({
            url: '/generate_response',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                user_id: '12345',
                query: query,
                preferred_language: 'en'
            }),
            success: function(response) {
                $('#ai_response').text(response.response);
                $('#sentiment_analysis').text(`${response.sentiment.label}: ${response.sentiment.score.toFixed(2)}`);
            },
            error: function(error) {
                console.error("Error:", error);
                $('#ai_response').text("An error occurred. Please try again.");
                $('#sentiment_analysis').text("");
            }
        });
    });
});
