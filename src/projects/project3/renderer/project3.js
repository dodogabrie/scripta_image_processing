fetch('../projects/project3/renderer/components/componentManager.js')
  .then(() => {
    console.log('Component manager loaded successfully');
    return true;
  })
  .then((componentsReady) => {
    if (componentsReady) {
      fetch('../projects/project3/renderer/project3.template.html')
        .then(response => response.text())
        .then(template => {
          window.project3 = {
            name: 'project3',
            template,
            data() {
              return {
                resources: [],
                newResourceName: '',
                toastMessage: '',
              };
            },
            methods: {
              // Resources
              addResource(resourceName) {
                if (!resourceName) {
                  this.toastMessage = 'Il nome della risorsa è obbligatorio.';
                  return;
                }
                const newResource = { name: resourceName, fields: [], children: [], newChildName: '' };
                this.resources.push(newResource);
                this.newResourceName = ''; // Reset input
              },
              removeResource(idx) {
                this.resources.splice(idx, 1);
              },
              addResourceField(rIdx, fieldName, fieldType) {
                if (!fieldName || !fieldType) {
                  this.toastMessage = 'Nome e tipo del campo sono obbligatori.';
                  return;
                }
                const newField = { name: fieldName, type: fieldType };
                this.resources[rIdx].fields.push(newField);
              },
              removeResourceField(rIdx, fIdx) {
                this.resources[rIdx].fields.splice(fIdx, 1);
              },
              addChildResource(rIdx, childName) {
                if (!childName) {
                  this.toastMessage = 'Il nome della risorsa figlia è obbligatorio.';
                  return;
                }
                const parentResource = this.resources[rIdx];
                const newChild = { name: childName, fields: [] };
                parentResource.children.push(newChild);
                parentResource.newChildName = ''; // Reset input
              },
              exportSchema() {
                const schema = {
                  resources: this.resources,
                };
                const blob = new Blob([JSON.stringify(schema, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'schema.json';
                a.click();
                URL.revokeObjectURL(url);
              },
            },
          };
        });
    } else {
      console.error('Failed to load components, cannot initialize project3.');
    }
  });
