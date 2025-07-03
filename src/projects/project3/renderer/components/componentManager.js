function loadComponents() {
  return Promise.all([
    fetch('../projects/project3/renderer/components/toastMessage/toastMessage.js')
      .then(() => {
        console.log('Toast-message component loaded successfully');
      })
      .catch((error) => {
        console.error('Error loading toast-message component:', error);
      }),
    // Add other component fetches here if needed
  ]).then(() => {
    console.log('All components are loaded and ready to use.');
    return true;
  }).catch((error) => {
    console.error('Error loading components in componentManager:', error);
    return false;
  });
}

export default loadComponents;
