fetch('../projects/project3/renderer/components/toastMessage/toastMessage.html')
  .then(response => {
    if (!response.ok) {
      throw new Error(`Failed to load toast-message template: ${response.statusText}`);
    }
    return response.text();
  })
  .then(template => {
    console.log('Toast-message component template loaded successfully');
    Vue.component('toast-message', {
      props: ['message'],
      template,
      methods: {
        showToast(message) {
          this.message = message;
          setTimeout(() => {
            this.message = '';
          }, 3000);
        },
        clearToast() {
          this.message = '';
        },
      },
    });
  })
  .catch(error => {
    console.error('Error loading toast-message component:', error);
  });
