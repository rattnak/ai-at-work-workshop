document.querySelectorAll('[data-copy]').forEach((button) => {
  button.addEventListener('click', async () => {
    const text = document.getElementById(button.dataset.copy).textContent;
    try {
      await navigator.clipboard.writeText(text);
      button.textContent = 'Copied!';
    } catch {
      button.textContent = 'Select and copy the text above';
    }
    window.setTimeout(() => { button.textContent = 'Copy prompt'; }, 3000);
  });
});
