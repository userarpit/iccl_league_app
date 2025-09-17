document.addEventListener("DOMContentLoaded", function () {
    const isPlayedCheckbox = document.getElementById("id_is_played");
    const isWalkoverCheckbox = document.getElementById("id_is_walkover");

    // Select the parent rows for more reliable hiding
    const isPlayedRow = isPlayedCheckbox ? isPlayedCheckbox.closest('.form-row') : null;
    const isWalkoverRow = isWalkoverCheckbox ? isWalkoverCheckbox.closest('.form-row') : null;

    const homeScoreRow = document.querySelector(".form-row.field-home_score");
    const awayScoreRow = document.querySelector(".form-row.field-away_score");
    const momRow = document.querySelector(".form-row.field-mom");
    const cardInline = document.querySelector("#cards-group");
    const goalsInline = document.querySelector("#goals-group");
    const walkoverWinnerRow = document.querySelector(".form-row.field-walkover_winner");

    // Log elements to the console for debugging
    console.log('isPlayedRow:', isPlayedRow);
    console.log('isWalkoverRow:', isWalkoverRow);
    console.log('walkoverWinnerRow:', walkoverWinnerRow);
    console.log('homeScoreRow:', homeScoreRow);

    function toggleFields() {
        if (!isPlayedCheckbox || !isWalkoverCheckbox) return; // Ensure elements exist

        const isPlayedChecked = isPlayedCheckbox.checked;
        const isWalkoverChecked = isWalkoverCheckbox.checked;

        // Reset visibility for all fields first
        if (isPlayedRow) isPlayedRow.style.display = '';
        if (isWalkoverRow) isWalkoverRow.style.display = '';
        if (walkoverWinnerRow) walkoverWinnerRow.style.display = 'none';
        if (homeScoreRow) homeScoreRow.style.display = 'none';
        if (awayScoreRow) awayScoreRow.style.display = 'none';
        if (momRow) momRow.style.display = 'none';
        if (cardInline) cardInline.style.display = 'none';
        if (goalsInline) goalsInline.style.display = 'none';
        
        // Logic for which fields to display
        if (isPlayedChecked) {
            if (isWalkoverRow) isWalkoverRow.style.display = 'none';
            if (walkoverWinnerRow) walkoverWinnerRow.style.display = 'none';
            if (homeScoreRow) homeScoreRow.style.display = '';
            if (awayScoreRow) awayScoreRow.style.display = '';
            if (momRow) momRow.style.display = '';
            if (cardInline) cardInline.style.display = '';
            if (goalsInline) goalsInline.style.display = '';
        } else if (isWalkoverChecked) {
            if (isPlayedRow) isPlayedRow.style.display = 'none';
            if (walkoverWinnerRow) walkoverWinnerRow.style.display = '';
            if (homeScoreRow) homeScoreRow.style.display = 'none';
            if (awayScoreRow) awayScoreRow.style.display = 'none';
            if (momRow) momRow.style.display = 'none';
            if (cardInline) cardInline.style.display = 'none';
            if (goalsInline) goalsInline.style.display = 'none';
        } else {
            // Neither is checked, all related fields are hidden
            if (walkoverWinnerRow) walkoverWinnerRow.style.display = 'none';
            if (homeScoreRow) homeScoreRow.style.display = 'none';
            if (awayScoreRow) awayScoreRow.style.display = 'none';
            if (momRow) momRow.style.display = 'none';
            if (cardInline) cardInline.style.display = 'none';
            if (goalsInline) goalsInline.style.display = 'none';
        }
    }


    // Initial run on page load
    toggleFields();

    // Attach event listeners
    if (isPlayedCheckbox) {
        isPlayedCheckbox.addEventListener('change', toggleFields);
    }
    if (isWalkoverCheckbox) {
        isWalkoverCheckbox.addEventListener('change', toggleFields);
    }
});