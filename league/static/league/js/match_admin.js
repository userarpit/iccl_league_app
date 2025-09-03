document.addEventListener("DOMContentLoaded", function () {
    const isPlayedCheckbox = document.querySelector("#id_is_played");
    const homeScoreRow = document.querySelector(".form-row.field-home_score");
    const awayScoreRow = document.querySelector(".form-row.field-away_score");
    const momRow = document.querySelector(".form-row.field-mom");
    const cardInline = document.querySelector("#cards-group");  // ✅ correct id from your screenshot
    const goalsInline = document.querySelector("#goals-group"); // goals inline block

    function toggleFields() {
        if (isPlayedCheckbox.checked) {
            homeScoreRow.style.display = "";
            awayScoreRow.style.display = "";
            momRow.style.display = "";
            if (cardInline) cardInline.style.display = "";   // show Cards inline
            if (goalsInline) goalsInline.style.display = "";
        } else {
            homeScoreRow.style.display = "none";
            awayScoreRow.style.display = "none";
            momRow.style.display = "none";
            if (cardInline) cardInline.style.display = "none"; // hide Cards inline
            if (goalsInline) goalsInline.style.display = "none";
        }
    }

    if (isPlayedCheckbox) {
        toggleFields(); // run on page load
        isPlayedCheckbox.addEventListener("change", toggleFields);
    }
});
