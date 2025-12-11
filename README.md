# Spécifications Fonctionnelles et Techniques - Agentic Platform

**Version** : Alpha 1.0 (Frozen)
**Date** : 2025-12-11

Ce document de référence présente une vue d'ensemble de l'application "Agentic Platform", détaillant ses fonctionnalités, son architecture technique, et son implémentation.

## 1. Résumé Fonctionnel

L'application est une plateforme "Low-Code" locale permettant de concevoir, configurer et exécuter des agents intelligents basés sur des LLM (Large Language Models). Elle est distribuée sous la forme d'un exécutable de bureau (Electron).

### Fonctionnalités Principales

*   **Smart Nodes & Optimisation (NOUVEAU 🌟)** :
    *   **Nœud Intelligent** : Configuration flexible des entrées et sorties (sans prompt engineering manuel).
    *   **Training Data** : Import de données d'entraînement via CSV (Copier-coller ou Upload) avec mapping automatique des colonnes.
    *   **Optimisation Automatique** : Utilisation du Framework **DSPy** pour optimiser les prompts ("Compile & Optimize") sur la base d'exemples.
    *   **Configuration Avancée** : Réglage du nombre de rounds d'optimisation (1 à 50) pour contrôler la profondeur de recherche.

*   **Gestion des Profils LLM (Settings)** :
    *   **Multi-Provider** : Support unifié pour OpenAI, Anthropic, Azure, et **Local LLMs** (Ollama, LM Studio).
    *   **Sécurité** : Stockage chiffré des clés API locales (via `keyring`).
    *   **Test de Connexion** : Validation immédiate des credentials.

*   **Éditeur Graphique d'Agents (Canvas)** :
    *   Interface visuelle (basée sur des nœuds et des arcs) pour concevoir le flux d'exécution.
    *   Support de différents types de nœuds : Agent, Smart Node, Outils, Routeurs logiques.

*   **Exécution de Flux (Run)** :
    *   Lancement des agents directement depuis l'interface via WebSocket.
    *   Visualisation en temps réel (streaming tokens, mise en surbrillance).

---

## 2. Architecture Technique

### Vue d'ensemble Stack

*   **Application Desktop** : [Electron](https://www.electronjs.org/).
*   **Frontend** : [React](https://react.dev/) + [Vite](https://vitejs.dev/) + [TailwindCSS](https://tailwindcss.com/).
    *   **Graphe UI** : React Flow (@xyflow/react).
*   **Backend** : [Python](https://www.python.org/) + [FastAPI](https://fastapi.tiangolo.com/).
    *   **Orchestration** : [LangChain](https://www.langchain.com/) & [LangGraph](https://langchain-ai.github.io/langgraph/).
    *   **Optimisation** : [DSPy](https://dspy.ai/) (v3.0+).
    *   **Base de Données** : SQLite (via `SQLModel`).

### Patrons de Conception (Design Patterns)

1.  **LangChain-First Architecture** :
    *   Utilisation de `dspy.LM` unifié pour interagir avec tous les modèles via LangChain/Community adapters.
2.  **Compiler Pattern** :
    *   Transformation du graphe JSON en `StateGraph` exécutable.
    *   Compilation des Smart Nodes en modules DSPy optimisés (sauvegardés en JSON).
3.  **Context-Safe Async** :
    *   Utilisation de `dspy.context` pour garantir la thread-safety des paramètres globaux dans un environnement asynchrone (FastAPI).

---

## 3. Implémentation Technique Détaillée

### 3.1. Moteur DSPy & Smart Nodes
L'implémentation repose sur `backend/app/engine/dspy_optimizer.py` et `dspy_utils.py`.
*   **BootstrapFewShot** : Algorithme utilisé pour sélectionner les meilleurs exemples ("Few-Shot") et optimiser la performance.
*   **Métriques** : Actuellement basé sur `ExactMatch` (comparaison stricte sortie attendue vs réelle).
*   **Persistence** : Les programmes compilés sont stockés dans `resources/smart_nodes/{node_id}_compiled.json`. Le Smart Node charge ce fichier à l'exécution s'il existe.

### 3.2. Gestion des Modèles
*   **Modèle `LLMProfile`** : Stocke provider, model_id, base_url.
*   **Providers Supportés** :
    *   `openai`, `anthropic`, `azure`.
    *   `ollama_chat` (via LangChain).
    *   `lm_studio` (compatible OpenAI API, port 1234 par défaut).

### 3.3. API & Communication
*   **REST** : Endpoints CRUD pour les modèles, endpoint `/optimize` pour lancer le training DSPy.
*   **WebSocket** : Streaming temps réel des tokens et événements d'exécution.

---

## 4. Roadmap & Futur (Beta)

### 4.1. Améliorations DSPy
*   **LLM-as-a-Judge** : Remplacer "Exact Match" par un juge IA pour évaluer des réponses subjectives.
*   **Auto-Labeling** : Permettre l'optimisation avec seulement des Inputs (le Teacher génère les Outputs).
*   **MIPRO** : Intégrer des optimiseurs avancés qui réécrivent aussi les instructions (pas seulement les exemples).

### 4.2. Packaging & Distribution
*   Générer les installateurs finaux `.exe` et `.dmg` (actuellement en mode dev).
*   Signature de code pour éviter les alertes de sécurité Windows/Mac.
