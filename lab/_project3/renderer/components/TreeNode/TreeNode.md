# Documentazione Sistema TreeNode

## Panoramica

Il sistema `TreeNode` è un insieme di componenti Vue.js modulari progettati per costruire strutture dati gerarchiche con diversi tipi di campi. Il sistema è stato refactorizzato in sottocomponenti per migliorare la manutenibilità, la leggibilità e il riuso del codice.

## Architettura Modulare

### Componenti Principali

#### 1. `TreeNode.vue` - Componente Router
Il componente principale che decide quale sottocomponente renderizzare basandosi sul tipo di nodo.

**Responsabilità:**
- Routing tra `TreeNodeContainer` e `TreeNodeField`
- Propagazione eventi tra i sottocomponenti e il componente padre

#### 2. `TreeNodeContainer.vue` - Contenitore Nodi
Gestisce i nodi contenitore che possono avere figli.

**Responsabilità:**
- Renderizzazione del layout del nodo contenitore
- Integrazione con `TreeNodeAddControls`
- Gestione ricorsiva dei nodi figli

#### 3. `TreeNodeField.vue` - Gestione Campi
Gestisce tutti i tipi di campi con le loro configurazioni specifiche.

**Responsabilità:**
- Renderizzazione comune dei campi (header, badge, bottone elimina)
- Routing verso i componenti di configurazione specifici per tipo

#### 4. `TreeNodeAddControls.vue` - Controlli Aggiunta
Componente dedicato per i controlli di aggiunta nodi e campi.

**Responsabilità:**
- Input per nome nodo/campo
- Selezione tipo campo
- Validazione input (disabilita bottoni se vuoti)
- Supporto Enter key per aggiunta rapida

#### 5. `FieldChoicesConfig.vue` - Configurazione Campi Scelta
Gestisce la configurazione dei campi di tipo scelta.

**Responsabilità:**
- Aggiunta/rimozione opzioni
- Validazione duplicati
- Feedback visivo per stati vuoti

#### 6. `FieldNumericConfig.vue` - Configurazione Campi Numerici
Gestisce la configurazione dei campi numerici.

**Responsabilità:**
- Configurazione min/max
- Gestione mapping numero-testo
- Sincronizzazione stato locale/globale
- Informazioni di validazione

## Caratteristiche del Sistema

- **Struttura Ricorsiva**: Annidamento infinito di nodi e campi
- **Architettura Modulare**: Componenti separati per responsabilità specifiche
- **Tipi di Campo Multipli**: Testo, Scelte e Numerico con configurazioni specializzate
- **Validazione Migliorata**: Input disabilitati per stati non validi
- **UX Migliorata**: Supporto Enter key, feedback visivo, aria-labels
- **Pronto per l'Export**: Formato dati strutturato adatto per l'esportazione JSON
- **UI Bootstrap**: Interfaccia pulita e responsiva con tipi di campo codificati per colore

## Vantaggi dell'Architettura Modulare

### 1. **Manutenibilità**
- Ogni componente ha una responsabilità specifica
- Più facile individuare e fixare bug
- Codice più leggibile e organizzato

### 2. **Riusabilità**
- I sottocomponenti possono essere riutilizzati indipendentemente
- Configurazioni specifiche isolate nei rispettivi componenti

### 3. **Testabilità**
- Ogni componente può essere testato isolatamente
- Mocking più semplice delle dipendenze

### 4. **Scalabilità**
- Facile aggiungere nuovi tipi di campo
- Nuove funzionalità possono essere aggiunte senza modificare altri componenti

### 5. **Performance**
- Componenti più piccoli = re-rendering più efficiente
- Lazy loading possibile per componenti specifici

## Tipi di Nodo

### 1. Nodo (`type !== 'field'`)
Elementi contenitore che possono contenere nodi figlio e campi.

**Proprietà:**
- `id`: Identificatore unico (generato automaticamente)
- `name`: Nome visualizzato
- `type`: Impostato a 'node'
- `children`: Array di nodi/campi figlio

**Capacità:**
- Aggiungere nodi figlio
- Aggiungere campi di qualsiasi tipo
- Eliminare nodo (rimuove tutti i figli)

### 2. Campo (`type === 'field'`)
Elementi di inserimento dati con comportamenti specifici per tipo.

**Proprietà:**
- `id`: Identificatore unico (generato automaticamente)
- `name`: Nome visualizzato
- `type`: Impostato a 'field'
- `fieldType`: Tipo di campo ('text', 'choices', 'numeric')
- `config`: Oggetto di configurazione specifico del campo
- `values`: Array di valori inseriti (nota: non incluso nell'export)
- `children`: Array di sotto-campi

## Tipi di Campo

### Campi Testo (`fieldType: 'text'`)

**Scopo**: Input di testo libero con supporto per valori multipli.

**Configurazione**: Nessuna configurazione richiesta.

**Caratteristiche**:
- Valori di testo multipli
- Nessun vincolo di validazione
- Interfaccia di input semplice

**Struttura di Esempio**:
```json
{
  "name": "Descrizione",
  "type": "field",
  "fieldType": "text",
  "config": {}
}
```

### Campi Scelta (`fieldType: 'choices'`)

**Scopo**: Selezione a scelta multipla con opzioni predefinite.

**Configurazione**:
- `options`: Array di scelte disponibili
- `multiSelect`: Boolean - permette selezioni multiple (non implementato nell'UI attuale)

**Caratteristiche**:
- Lista opzioni configurabile
- Gestione dinamica delle opzioni
- Interfaccia di selezione visuale

**Struttura di Esempio**:
```json
{
  "name": "Stato",
  "type": "field",
  "fieldType": "choices",
  "config": {
    "options": ["Attivo", "Inattivo", "In Sospeso"]
  }
}
```

### Campi Numerici (`fieldType: 'numeric'`)

**Scopo**: Input numerico con validazione e vincoli.

**Configurazione**:
- `min`: Valore minimo consentito
- `max`: Valore massimo consentito  
- `mapping`: Oggetto che mappa numeri a testi descrittivi

**Caratteristiche**:
- Validazione range min/max
- Mapping numero-testo per descrizioni
- Interfaccia di input numerica

**Struttura di Esempio**:
```json
{
  "name": "Valutazione",
  "type": "field",
  "fieldType": "numeric",
  "config": {
    "min": 1,
    "max": 5,
    "mapping": {
      "1": "Scarso",
      "2": "Sufficiente",
      "3": "Buono",
      "4": "Ottimo",
      "5": "Eccellente"
    }
  }
}
```

### Numeric Fields (`fieldType: 'numeric'`)

**Purpose**: Number input with validation and constraints.

**Configuration Types**:

#### Integer (`numericType: 'integer'`)
- `min`: Minimum allowed value
- `max`: Maximum allowed value
- Validates whole numbers only

#### Float (`numericType: 'float'`)
- `min`: Minimum allowed value
- `max`: Maximum allowed value
- Allows decimal numbers

#### Range (`numericType: 'range'`)
- `availableNumbers`: Array of specific allowed numbers
- `allowDecimals`: Boolean - permits decimal values in the range

**Example Structures**:

```json
// Integer field
{
  "id": "field3",
  "name": "Age",
  "type": "field",
  "fieldType": "numeric",
  "config": {
    "numericType": "integer",
    "min": 0,
    "max": 120
  },
  "values": [25, 30]
}

// Range field
{
  "id": "field4",
  "name": "Rating",
  "type": "field",
  "fieldType": "numeric",
  "config": {
    "numericType": "range",
    "availableNumbers": [1, 2, 3, 4, 5],
    "allowDecimals": false
  },
  "values": [4, 5]
}
```

## Eventi

Il componente emette i seguenti eventi che i componenti padre devono gestire:

### Gestione Nodi
- `add-child(parentId, childName)`: Aggiunge un nuovo nodo figlio
- `add-field(parentId, fieldName, fieldType, fieldConfig)`: Aggiunge un nuovo campo
- `delete-node(nodeId)`: Elimina un nodo o campo

### Gestione Configurazioni
- `update-config({ node, config })`: Aggiorna la configurazione di un campo

### Gestione Valori
- `add-value(fieldId, value)`: Aggiunge un valore a un campo
- `remove-value(fieldId, valueIndex)`: Rimuove un valore da un campo
- `update-field-config(fieldId, config)`: Aggiorna la configurazione del campo

## Utilizzo dei Componenti

### TreeNode (Router Principale)
```vue
<TreeNode 
  :node="node"
  @add-child="handleAddChild"
  @add-field="handleAddField" 
  @delete-node="handleDeleteNode"
  @update-config="handleUpdateConfig"
/>
```

### TreeNodeContainer (Uso Diretto)
```vue
<TreeNodeContainer
  :node="containerNode"
  @add-child="handleAddChild"
  @add-field="handleAddField"
  @delete-node="handleDeleteNode"
/>
```

### TreeNodeField (Uso Diretto)
```vue
<TreeNodeField
  :node="fieldNode"
  @delete-node="handleDeleteNode"
  @update-config="handleUpdateConfig"
/>
```

### TreeNodeAddControls (Standalone)
```vue
<TreeNodeAddControls
  @add-child="handleAddChild"
  @add-field="handleAddField"
/>
```

### Componenti di Configurazione Campo
```vue
<!-- Per campi scelta -->
<FieldChoicesConfig
  :node="choiceField"
  @update-config="handleUpdateConfig"
/>

<!-- Per campi numerici -->
<FieldNumericConfig
  :node="numericField"
  @update-config="handleUpdateConfig"
/>
```

### Import dalla Nuova Struttura

#### Import Semplice (Raccomandato)
```javascript
// Import del sistema completo
import TreeNode from './components/TreeNode/TreeNodeSystem';

// Import diretto del componente principale
import TreeNode from './components/TreeNode/TreeNode.vue';
```

#### Import Selettivi
```javascript
// Import componenti specifici
import TreeNodeContainer from './components/TreeNode/TreeNodeContainer.vue';
import TreeNodeField from './components/TreeNode/Fields/TreeNodeField.vue';
import TreeNodeAddControls from './components/TreeNode/AddNode/TreeNodeAddControls.vue';

// Import configurazioni campi
import FieldChoicesConfig from './components/TreeNode/Fields/FieldChoicesConfig.vue';
import FieldNumericConfig from './components/TreeNode/Fields/FieldNumericConfig.vue';

// Import utilità JSON
import ImportTreeData from './components/TreeNode/TreeNodeJson/ImportTreeData.vue';
import ExportTreeData from './components/TreeNode/TreeNodeJson/ExportTreeData.vue';

// Import utilities
import { TreeExporter, TreeImporter, TreeValidator } from './components/TreeNode/TreeNodeUtils.js';
```

#### Import tramite TreeNodeSystem
```javascript
// Import raggruppati tramite il sistema
import { 
  TreeNodeComponents, 
  TreeDataComponents, 
  TreeUtilities 
} from './components/TreeNode/TreeNodeSystem';

// Destructuring per componenti specifici
const { TreeNodeContainer, TreeNodeField } = TreeNodeComponents;
const { ImportTreeData, ExportTreeData } = TreeDataComponents;
const { TreeExporter, TreeValidator } = TreeUtilities;
```

## Esempio di Utilizzo

### Implementazione Base

```vue
<template>
  <div>
    <TreeNode 
      :node="rootNode" 
      @add-child="handleAddChild"
      @add-field="handleAddField"
      @delete-node="handleDeleteNode"
      @update-config="handleUpdateConfig"
    />
  </div>
</template>

<script>
import { v4 as uuidv4 } from "uuid";
import TreeNode from './components/TreeNode.vue';

export default {
  components: { TreeNode },
  data() {
    return {
      rootNodes: []
    };
  },
  methods: {
    addRootNode() {
      this.rootNodes.push({
        id: uuidv4(),
        name: "Nuovo Elemento Radice",
        type: "node",
        children: []
      });
    },

    handleAddChild(parentId, childName) {
      const parent = this.findNodeById(parentId);
      if (parent) {
        parent.children.push({
          id: uuidv4(),
          name: childName,
          type: "node",
          children: []
        });
      }
    },
    
    handleAddField(parentId, fieldName, fieldType, fieldConfig) {
      const parent = this.findNodeById(parentId);
      if (parent) {
        parent.children.push({
          id: uuidv4(),
          name: fieldName,
          type: "field",
          fieldType,
          config: fieldConfig,
          values: [],
          children: []
        });
      }
    },
    
    handleDeleteNode(nodeId) {
      this.deleteNode(nodeId);
    },
    
    handleUpdateConfig({ node, config }) {
      node.config = { ...config };
    },

    findNodeById(targetId, nodes = this.rootNodes) {
      for (const node of nodes) {
        if (node.id === targetId) {
          return node;
        }
        if (node.children?.length) {
          const found = this.findNodeById(targetId, node.children);
          if (found) return found;
        }
      }
      return null;
    },
    
    deleteNode(nodeId, nodes = this.rootNodes) {
      for (let i = 0; i < nodes.length; i++) {
        if (nodes[i].id === nodeId) {
          nodes.splice(i, 1);
          return true;
        }
        if (nodes[i].children?.length && this.deleteNode(nodeId, nodes[i].children)) {
          return true;
        }
      }
      return false;
    }
  }
};
</script>
```

## Funzionalità di Export/Import

### Struttura Dati per l'Export

Il componente crea una struttura JSON gerarchica che preserva:
- Relazioni tra nodi e annidamenti
- Tipi di campo e configurazioni
- **NOTA**: Gli ID e i values NON sono inclusi nell'export per mantenere solo la struttura del modello

### Esempio di Export

```json
{
  "version": "1.0",
  "exportDate": "2025-07-21T10:30:00.000Z",
  "data": {
    "name": "Sistema Cartelle Mediche",
    "type": "node",
    "children": [
      {
        "name": "Informazioni Paziente",
        "type": "node",
        "children": [
          {
            "name": "Nome Completo",
            "type": "field",
            "fieldType": "text",
            "config": {}
          },
          {
            "name": "Età",
            "type": "field",
            "fieldType": "numeric",
            "config": {
              "min": 0,
              "max": 150,
              "mapping": {}
            }
          },
          {
            "name": "Gruppo Sanguigno",
            "type": "field",
            "fieldType": "choices",
            "config": {
              "options": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
            }
          }
        ]
      }
    ]
  },
  "metadata": {
    "rootName": "Sistema Cartelle Mediche",
    "created": "2025-07-21T10:30:00.000Z",
    "structure": "hierarchical",
    "fieldTypes": ["text", "choices", "numeric"]
  },
  "stats": {
    "totalNodes": 1,
    "totalFields": 3,
    "fieldTypes": {
      "text": 1,
      "numeric": 1,
      "choices": 1
    },
    "maxDepth": 2,
    "totalValues": 0
  }
}
```

### Import

Durante l'import:
- Gli ID vengono rigenerati automaticamente
- I values vengono inizializzati come array vuoti
- La struttura e le configurazioni vengono preservate
- Viene eseguita la validazione della struttura importata

## Regole di Validazione

### Campi Testo
- Nessuna validazione applicata
- Tutti i valori stringa sono accettati

### Campi Scelta
- Le opzioni devono essere configurate nell'array `options`
- Supporto per gestione dinamica delle opzioni

### Campi Numerici
- I valori devono essere numeri validi
- Rispettano i vincoli min/max quando impostati
- Supportano mapping personalizzato numero-testo

## Stile e Temi

Il componente utilizza classi Bootstrap con CSS personalizzato per:
- Tipi di campo codificati per colore
- Layout responsivo
- Effetti hover e transizioni
- Controlli form compatti per strutture annidate

### Colori per Tipo di Campo
- **Nodi**: Header blu con gradiente
- **Campi Testo**: Bordo blu (`border-info`)
- **Campi Scelta**: Bordo verde (`border-success`)  
- **Campi Numerici**: Bordo giallo (`border-warning`)

## Migliori Pratiche

### Performance
- Utilizzare ID unici per tutti i nodi/campi (gestito automaticamente)
- Implementare algoritmi di ricerca efficienti per alberi grandi
- Considerare lo scrolling virtuale per gerarchie molto profonde

### Gestione Dati
- Implementare funzionalità di undo/redo per l'esperienza utente
- Auto-salvataggio regolare per la persistenza dei dati
- Export periodici per backup della struttura

### Esperienza Utente
- Fornire feedback visivo chiaro per i tipi di campo
- Utilizzare controlli di input appropriati per ogni tipo di campo
- Implementare scorciatoie da tastiera per azioni comuni

## Risoluzione Problemi

### Problemi Comuni
1. **Configurazione campo mancante**: Il componente inizializza automaticamente le configurazioni mancanti
2. **Valori numerici non validi**: La validazione previene inserimenti non validi
3. **Riferimenti circolari**: Evitare di creare loop padre-figlio
4. **Performance**: Limitare i livelli di annidamento profondi per prestazioni ottimali

### Debug
- Abilitare gli strumenti dev di Vue per l'ispezione dei componenti
- Utilizzare la console del browser per ispezionare la struttura dei nodi
- Validare i dati di export prima dell'elaborazione esterna

## Utilities Disponibili

Il file `TreeNodeUtils.js` fornisce classi utility per:

### TreeTraversal
- `findNodeById()`: Trova un nodo per ID
- `getNodesByType()`: Ottiene tutti i nodi di un tipo specifico
- `getTreeStats()`: Calcola statistiche dell'albero

### TreeValidator  
- `validateTree()`: Valida una struttura ad albero completa
- `validateFieldValue()`: Valida un singolo valore di campo
- `validateFieldConfig()`: Valida la configurazione di un campo

### TreeExporter
- `exportToJSON()`: Esporta in JSON con metadati
- `exportDataOnly()`: Esporta solo i valori dei dati
- `exportToCSV()`: Esporta come CSV (struttura appiattita)

### TreeImporter
- `importFromJSON()`: Importa da JSON con validazione

### TreeManipulator
- `cloneTree()`: Clona una struttura ad albero
- `addNode()`: Aggiunge un nodo a un genitore
- `removeNode()`: Rimuove un nodo per ID
- `moveNode()`: Sposta un nodo a un nuovo genitore

## Miglioramenti UX nella Versione Modulare

### 1. **Validazione Input Migliorata**
- I pulsanti di aggiunta sono disabilitati quando i campi sono vuoti
- Feedback visivo immediato sullo stato dei controlli
- Prevenzione di inserimenti accidentali

### 2. **Supporto Tastiera**
- **Enter** nei campi di input attiva l'aggiunta
- Navigazione più fluida per utenti esperti
- Accessibilità migliorata

### 3. **Feedback Visivo**
- Stati vuoti chiaramente indicati con testo descrittivo
- Aria-labels per screen readers
- Informazioni di validazione per campi numerici

### 4. **Gestione Stato Migliorata**
- Sincronizzazione automatica tra stato locale e globale
- Watch reattivi per aggiornamenti esterni
- Gestione delle configurazioni più robusta

### 5. **Organizzazione Visiva**
- Componenti più focalizzati con responsabilità chiare
- Spacing e layout ottimizzati
- Colorazione consistente tra tutti i sottocomponenti

## File Structure del Sistema

```
components/TreeNode/
├── TreeNode.vue              # Router principale
├── TreeNodeContainer.vue     # Gestione nodi contenitore
├── TreeNodeSystem.js         # File indice per export
├── TreeNodeUtils.js          # Utilities e validazione
├── TreeNode.md              # Documentazione
├── AddNode/
│   └── TreeNodeAddControls.vue   # Controlli aggiunta
├── Fields/
│   ├── TreeNodeField.vue         # Gestione campi base
│   ├── FieldChoicesConfig.vue    # Config campi scelta
│   └── FieldNumericConfig.vue    # Config campi numerici
└── TreeNodeJson/
    ├── ImportTreeData.vue        # Importazione dati
    └── ExportTreeData.vue        # Esportazione dati
```

## Migration dalla Versione Monolitica

Il passaggio dalla versione monolitica a quella modulare è **backward compatible**:

### Per Utenti Esistenti
```vue
<!-- Questo codice continua a funzionare -->
<TreeNode 
  :node="node"
  @add-child="handleAddChild"
  @add-field="handleAddField"
  @delete-node="handleDeleteNode"
  @update-config="handleUpdateConfig"
/>
```

### Per Nuovi Progetti
```vue
<!-- Raccomandato: import semplificato -->
import TreeNode from './components/TreeNode/TreeNodeSystem';

<!-- Oppure: import selettivo per uso avanzato -->
import { TreeNodeContainer, TreeDataComponents } from './components/TreeNode/TreeNodeSystem';
```

## Modifiche Recenti

- **Riorganizzazione Struttura**: I componenti sono ora organizzati in sottocartelle logiche:
  - `AddNode/` - Controlli per aggiungere nodi/campi
  - `Fields/` - Componenti per gestione campi e configurazioni
  - `TreeNodeJson/` - Funzionalità import/export
- **Refactor Modulare**: Il mega-componente è stato spezzato in 6 sottocomponenti specializzati
- **UX Migliorata**: Validazione input, supporto Enter key, feedback visivo
- **Manutenibilità**: Responsabilità separate, testing semplificato, codice più pulito
- **Export senza ID e Values**: L'export esclude ID tecnici e values per concentrarsi sulla struttura
- **Import migliorato**: Rigenerazione automatica degli ID durante l'import
- **Gestione eventi corretta**: Risolti problemi di propagazione eventi tra componenti
- **Architettura Future-Proof**: Facilmente estensibile per nuovi tipi di campo
- **Import Path Aggiornati**: Tutti i percorsi di import riflettono la nuova struttura organizzata