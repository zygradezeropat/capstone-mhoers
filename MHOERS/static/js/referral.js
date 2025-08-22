document.querySelectorAll(".nav-link").forEach((tab) => {
  tab.addEventListener("click", () => {
    setTimeout(() => {
      const activeTab = document.querySelector(".tab-pane.active");
      const saveButton = document.getElementById("saveReferralBtn");

      if (!activeTab || !saveButton) return;

      saveButton.style.display =
        activeTab.id === "exam" ? "inline-block" : "none";
    }, 10);
  });
});
