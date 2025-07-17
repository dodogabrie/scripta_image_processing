<template>
  <div id="app" class="d-flex flex-column vh-100">
    <!-- Header -->
    <nav class="navbar navbar-dark bg-primary">
      <div class="container-fluid">
        <span class="navbar-brand mb-0 h1">
          <i class="fas fa-project-diagram me-2"></i>
          Scripta Elaborazione Immagini
          <span v-if="currentProject" class="ms-2">
            - {{
              (projects.find(p => p.id === currentProject)?.config?.name) || currentProject
            }}
          </span>
        </span>
        <div class="d-flex align-items-center">
          <button v-if="currentProject" class="btn btn-outline-light btn-sm me-3" @click="goBackToHome">
            <i class="fas fa-arrow-left me-1"></i>
            Torna alla Home
          </button>
          <span class="badge bg-success me-2" v-if="appStatus.isReady">
            <i class="fas fa-check-circle me-1"></i>
            Pronto
          </span>
          <span class="badge bg-warning" v-else>
            <i class="fas fa-clock me-1"></i>
            Inizializzazione
          </span>
        </div>
      </div>
    </nav>

    <!-- Home View -->
    <div v-if="!currentProject" class="container-fluid flex-grow-1 p-4">
      <!-- Projects Grid -->
      <div class="row">
        <div class="col-12 mb-4">
          <h2>
            <i class="fas fa-folder-open me-2"></i>
            Progetti Disponibili
          </h2>
          <p class="text-muted">Seleziona un progetto per iniziare l'elaborazione delle immagini</p>
        </div>
      </div>

      <div class="row" v-if="projects.length > 0">
        <div class="col-lg-4 col-md-6 mb-4" v-for="project in projects" :key="project.id">
          <div class="card h-100 project-card">
            <div class="card-body d-flex flex-column">
              <div class="text-center mb-3">
                <template v-if="project.config.icon">
                  <img :src="project.iconDataUrl"
                       alt="Icona progetto"
                       style="max-width:48px;max-height:48px;" />
                </template>
                <template v-else>
                  <i class="fas fa-image fa-3x text-primary"></i>
                </template>
              </div>
              <h5 class="card-title text-center">{{ project.config.name }}</h5>
              <p class="card-text text-muted text-center flex-grow-1">
                {{ project.config.description }}
              </p>
              <div class="text-center">
                <span class="badge bg-secondary">v{{ project.config.version }}</span>
              </div>
            </div>
            <div class="card-footer bg-transparent">
              <button class="btn btn-primary w-100"
                      :disabled="!appStatus.isReady"
                      @click.stop="openProject(project.id)">
                <i class="fas fa-play me-2"></i>
                Apri Progetto
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- No Projects Message -->
      <div class="row" v-if="projects.length === 0 && projectsLoaded">
        <div class="col-12">
          <div class="card text-center">
            <div class="card-body py-5">
              <i class="fas fa-folder-open fa-4x text-muted mb-3"></i>
              <h3 class="text-muted">Nessun Progetto Trovato</h3>
              <p class="text-muted">
                Non sono stati trovati progetti nella cartella projects.<br>
                Crea un nuovo progetto per iniziare.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading Projects -->
      <div class="row" v-if="!projectsLoaded">
        <div class="col-12">
          <div class="card text-center">
            <div class="card-body py-5">
              <i class="fas fa-spinner fa-spin fa-3x text-primary mb-3"></i>
              <h3>Caricamento Progetti...</h3>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Project View -->
    <div v-if="currentProject" class="flex-grow-1" id="project-container">
      <component :is="currentProjectComponent" @goBack="goBackToHome" v-if="currentProjectComponent" />
    </div>
  </div>
</template>

<script>
import { markRaw } from 'vue';
const projectComponents = import.meta.glob('../projects/**/renderer/*.vue');
export default {
  name: 'App',
  data() {
    return {
      currentProject: null,
      projects: [],
      projectsLoaded: false,
      appStatus: {
        isReady: false,
      },
      currentProjectComponent: null,
    };
  },
  methods: {
    goBackToHome() {
      this.currentProject = null;
      this.currentProjectComponent = null;
    },
    async openProject(projectId) {
      const project = this.projects.find(p => p.id === projectId);
      if (!project) return;
      const componentPath = `../projects/${projectId}/${project.config.main}`;
      const loader = projectComponents[componentPath];
      if (!loader) {
        console.error('Componente non trovato:', componentPath);
        return;
      }

      const component = (await loader()).default;
      this.currentProject = projectId;
      this.currentProjectComponent = markRaw(component);
    }

  },
  mounted() {
    window.electronAPI.getProjects().then(async projects => {
      for (const project of projects) {
        const dataUrl = await window.electronAPI.getProjectIconData(project.id);
        project.iconDataUrl = dataUrl;
      }
      this.projects = projects;
      this.projectsLoaded = true;
      this.appStatus.isReady = true;
    });
  }

};
</script>

<style>
.project-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.project-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.project-card:active {
  transform: translateY(-2px);
}
</style>