import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
from models import QuestionDataset, QuizGenerator, QuizCorrector

# --- Configuration Streamlit ---
st.set_page_config(
    page_title="Quiz Wooclap Style", 
    layout="wide", 
    page_icon="✨",
    initial_sidebar_state="expanded"
)

# --- AJOUT: Classe QuizView comme demandé dans le README ---
class QuizView:
    """
    Classe pour gérer le rendu et les interactions Streamlit du quiz
    Conforme aux spécifications du README
    """
    
    def __init__(self, dataset, generator, corrector):
        self.dataset = dataset
        self.generator = generator
        self.corrector = corrector
        
    def render_sidebar(self):
        """Rendu de la barre latérale avec sélection des tags"""
        with st.sidebar:
            st.markdown("""
            <div style='text-align: center; margin-bottom: 2rem;'>
                <h2 style='color: #2563eb;'>⚙️ Configuration</h2>
            </div>
            """, unsafe_allow_html=True)
            
            tags = sorted(list(self.dataset.all_tags()))
            selected_tags = st.multiselect("**Choisis les thèmes :**", tags)
            n_questions = st.slider("**Nombre de questions :**", 5, 20, 10)
            
            if st.button("🚀 Générer le quiz", use_container_width=True):
                self.initialize_quiz(selected_tags, n_questions)
                st.rerun()
            
            st.markdown("---")
            
            # AJOUT: Affichage de l'historique dans la sidebar
            if st.session_state.get('quiz_history'):
                st.markdown("### 📊 Historique")
                history_summary = self._get_history_summary()
                st.metric("Quiz complétés", len(st.session_state.quiz_history))
                st.metric("Score moyen", f"{history_summary['avg_score']:.1f}%")
            
            st.markdown("""
            <div style='text-align: center; color: #64748b; margin-top: 2rem;'>
                <small>Quiz interactif avec analyse détaillée</small>
            </div>
            """, unsafe_allow_html=True)
            
            # AJOUT: Bouton reset plus visible
            if st.session_state.get('quiz_generated'):
                if st.button("🔄 Nouveau Quiz", use_container_width=True, type="secondary"):
                    self.reset_quiz()
                    st.rerun()
    
    def _get_history_summary(self):
        """Obtenir un résumé de l'historique"""
        if not st.session_state.quiz_history:
            return {"avg_score": 0, "best_score": 0, "total_quizzes": 0}
        
        scores = [quiz['total_score'] for quiz in st.session_state.quiz_history]
        return {
            "avg_score": sum(scores) / len(scores),
            "best_score": max(scores),
            "total_quizzes": len(scores)
        }
    
    def initialize_quiz(self, selected_tags, n_questions):
        """Initialiser un nouveau quiz"""
        st.session_state.quiz = self.generator.generate(selected_tags, n_questions)
        st.session_state.step = 0
        st.session_state.answers = {}
        st.session_state.selected_options = {}
        st.session_state.quiz_generated = True
        st.session_state.quiz_finished = False
    
    def reset_quiz(self):
        """Réinitialiser complètement le quiz (AJOUT: méthode structurée)"""
        # Ne pas supprimer l'historique lors de la réinitialisation
        quiz_history = st.session_state.get('quiz_history', [])
        for key in list(st.session_state.keys()):
            if key != 'quiz_history':  # Préserver l'historique
                del st.session_state[key]
        
        st.session_state.quiz_history = quiz_history
        st.session_state.step = 0
        st.session_state.answers = {}
        st.session_state.selected_options = {}
        st.session_state.quiz_generated = False
        st.session_state.quiz_finished = False
    
    def render_question(self, question, question_index, total_questions):
        """Rendu d'une question avec les widgets appropriés selon le type"""
        
        st.markdown(f"<div class='question-card'>Question {question_index + 1} sur {total_questions}<br><br>{question.question}</div>", unsafe_allow_html=True)

        # Barre de progression
        progress_pct = ((question_index + 1) / total_questions) * 100
        st.markdown(f"""
        <div class='progress-container'>
            <div style='display: flex; justify-content: space-between; margin-bottom: 0.5rem;'>
                <span style='color: #64748b;'>Progression</span>
                <span style='color: #2563eb; font-weight: bold;'>{question_index + 1}/{total_questions}</span>
            </div>
            <div class='progress-bar'>
                <div class='progress-fill' style='width:{progress_pct}%;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # CORRECTION: Utiliser votre interface originale avec boutons horizontaux
        self._render_options_with_buttons(question, question_index)
    
    def _render_options_with_buttons(self, question, question_index):
        """Rendu des options avec les boutons horizontaux (votre interface originale)"""
        
        # Initialiser les sélections
        if question_index not in st.session_state.selected_options:
            st.session_state.selected_options[question_index] = []

        # Options de réponse en boutons horizontaux
        cols = st.columns(2)
        for i, opt in enumerate(question.choices):
            col = cols[i % 2]
            is_selected = opt in st.session_state.selected_options.get(question_index, [])
            
            button_type = "primary" if is_selected else "secondary"
            
            if col.button(
                opt, 
                key=f"option-{question_index}-{i}",
                use_container_width=True,
                type=button_type
            ):
                self._toggle_option(question, question_index, opt)
                st.rerun()

        # Affichage des sélections actuelles
        if st.session_state.selected_options.get(question_index):
            st.success(f"✅ **Sélectionné(s) :** {', '.join(st.session_state.selected_options[question_index])}")
    
    def _toggle_option(self, question, question_index, option):
        """Basculer la sélection d'une option pour une question"""
        if question_index not in st.session_state.selected_options:
            st.session_state.selected_options[question_index] = []
        
        # Logique différente pour single vs multiple choice
        if question.is_single():
            # Single choice: une seule sélection possible
            st.session_state.selected_options[question_index] = [option]
        else:
            # Multiple choice: basculer la sélection
            if option in st.session_state.selected_options[question_index]:
                st.session_state.selected_options[question_index].remove(option)
            else:
                st.session_state.selected_options[question_index].append(option)
        
        st.session_state.answers[question_index] = st.session_state.selected_options[question_index]
    
    def render_navigation(self, current_index, total_questions):
        """Rendu de la navigation entre questions"""
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if current_index > 0:
                if st.button("⬅️ Précédent", use_container_width=True):
                    st.session_state.step -= 1
                    st.rerun()
        
        with col2:
            if st.button("🔄 Réinitialiser", use_container_width=True):
                st.session_state.selected_options[current_index] = []
                st.session_state.answers[current_index] = []
                st.rerun()
        
        with col3:
            if current_index < total_questions - 1:
                if st.button("Suivant ➡️", use_container_width=True, type="primary"):
                    st.session_state.step += 1
                    st.rerun()
            else:
                if st.button("✅ Terminer le quiz", use_container_width=True, type="primary"):
                    self.finish_quiz()
                    st.rerun()
    
    def finish_quiz(self):
        """Terminer le quiz et calculer les résultats"""
        # S'assurer que toutes les réponses sont enregistrées
        for i in range(len(st.session_state.quiz)):
            if i in st.session_state.selected_options:
                st.session_state.answers[i] = st.session_state.selected_options[i]
            elif i not in st.session_state.answers:
                st.session_state.answers[i] = []
        
        try:
            results = self.corrector.correct_quiz(st.session_state.quiz, st.session_state.answers)
            st.session_state.results = results
            
            # AJOUT: Sauvegarde dans l'historique
            self._save_to_history(results)
            
            # Stocker les questions et réponses pour l'affichage détaillé
            st.session_state.quiz_questions = st.session_state.quiz
            st.session_state.user_answers = st.session_state.answers.copy()
            
            module_stats = self.calculate_module_stats(st.session_state.quiz, results)
            st.session_state.module_stats = module_stats
            
            st.session_state.quiz_finished = True
        except Exception as e:
            st.error(f"Erreur lors de la correction : {e}")
    
    def _save_to_history(self, results):
        """AJOUT: Sauvegarder les résultats dans l'historique"""
        quiz_record = {
            "timestamp": datetime.now().isoformat(),
            "total_score": results['total_score'],
            "n_questions": len(st.session_state.quiz),
            "tags": list(set(tag for q in st.session_state.quiz for tag in q.tags)),
            "details": {
                "per_question": results['per_question'],
                "module_stats": self.calculate_module_stats(st.session_state.quiz, results)
            }
        }
        
        # Initialiser l'historique si nécessaire
        if "quiz_history" not in st.session_state:
            st.session_state.quiz_history = []
        
        st.session_state.quiz_history.append(quiz_record)
    
    def calculate_module_stats(self, questions, results):
        """Calculer les statistiques par module/thème"""
        module_scores = {}
        module_counts = {}
        
        for i, question in enumerate(questions):
            modules = getattr(question, 'tags', ['Général'])
            if not modules:
                modules = ['Général']
            
            for module in modules:
                if module not in module_scores:
                    module_scores[module] = 0
                    module_counts[module] = 0
                
                module_scores[module] += results['per_question'][i]['score']
                module_counts[module] += 1
        
        module_stats = []
        for module in module_scores:
            avg_score = (module_scores[module] / module_counts[module]) * 100
            module_stats.append({
                'module': module,
                'score': avg_score,
                'count': module_counts[module],
                'feedback': get_feedback(avg_score)
            })
        
        return sorted(module_stats, key=lambda x: x['score'], reverse=True)

# --- Chargement du dataset ---
@st.cache_resource
def load_dataset():
    ds = QuestionDataset("quiz_dataset.json")
    return ds

dataset = load_dataset()
generator = QuizGenerator(dataset)
corrector = QuizCorrector()
quiz_view = QuizView(dataset, generator, corrector)  # AJOUT: Instance de QuizView

# --- CSS Style Clair et Moderne ---
st.markdown("""
<style>
    /* Variables de couleurs claires */
    :root {
        --primary: #2563eb;
        --primary-light: #3b82f6;
        --secondary: #7c3aed;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --background: #f8fafc;
        --card-bg: #ffffff;
        --card-hover: #f1f5f9;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --border: #e2e8f0;
    }
    
    .main-header {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 1rem;
        padding: 1rem;
    }
    
    .sub-header {
        color: var(--text-secondary);
        text-align: center;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    .question-card {
        background: var(--card-bg);
        color: var(--text-primary);
        border-radius: 20px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        text-align: center;
        font-size: 1.4rem;
        font-weight: 600;
        border: 1px solid var(--border);
        transition: transform 0.3s ease;
    }
    
    .question-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    
    .option-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.2rem;
        margin-top: 2rem;
    }
    
    .option-card {
        background: var(--card-bg);
        border: 2px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem;
        cursor: pointer;
        text-align: center;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        min-height: 100px;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
        color: var(--text-primary);
    }
    
    .option-card:hover {
        transform: translateY(-3px);
        border-color: var(--primary);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.15);
        background: var(--card-hover);
    }
    
    .option-selected {
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
        border-color: var(--primary) !important;
        color: white !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.25);
    }
    
    .progress-container {
        background: var(--card-bg);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 2rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid var(--border);
    }
    
    .progress-bar {
        height: 10px;
        border-radius: 8px;
        background-color: #e2e8f0;
        margin: 15px 0;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        border-radius: 8px;
        transition: width 0.5s ease;
    }
    
    .nav-button {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 1.5rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 1rem;
    }
    
    .nav-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px20px rgba(37, 99, 235, 0.3);
    }
    
    .stats-card {
        background: var(--card-bg);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid var(--primary);
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: transform 0.3s ease;
        border: 1px solid var(--border);
    }
    
    .stats-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    }
    
    .result-badge {
        background: linear-gradient(135deg, var(--success), #059669);
        color: white;
        padding: 0.4rem 1.2rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }
    
    .history-card {
        background: var(--card-bg);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid var(--secondary);
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: transform 0.3s ease;
        border: 1px solid var(--border);
    }
    
    .history-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
    }
    
    .floating-element {
        animation: float 6s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-5px); }
    }
    
    /* Style pour Streamlit */
    .stButton > button {
        border-radius: 12px !important;
        padding: 0.8rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
    }
    
    /* Sidebar styling */
    .css-1d391kg, .css-1lcbmhc {
        background-color: #f8fafc;
    }
    
    .correct-answer {
        background: rgba(16, 185, 129, 0.1) !important;
        border: 2px solid #10b981 !important;
        color: #065f46 !important;
    }
    
    .user-answer {
        background: rgba(37, 99, 235, 0.1) !important;
        border: 2px solid #2563eb !important;
        color: #1e40af !important;
    }
    
    .incorrect-answer {
        background: rgba(239, 68, 68, 0.1) !important;
        border: 2px solid #ef4444 !important;
        color: #991b1b !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Initialisation session_state ---
if "step" not in st.session_state:
    st.session_state.step = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "quiz" not in st.session_state:
    st.session_state.quiz = None
if "selected_options" not in st.session_state:
    st.session_state.selected_options = {}
if "quiz_generated" not in st.session_state:
    st.session_state.quiz_generated = False
if "quiz_finished" not in st.session_state:
    st.session_state.quiz_finished = False
# AJOUT: Initialisation de l'historique
if "quiz_history" not in st.session_state:
    st.session_state.quiz_history = []
# AJOUT: Initialisation pour la vue détaillée de l'historique
if "viewing_history_quiz" not in st.session_state:
    st.session_state.viewing_history_quiz = None

# --- Fonctions utilitaires (conservées de votre code original) ---
def get_feedback(score):
    """Retourner un feedback et emoji selon le score"""
    if score >= 90:
        return "🎉 Excellent !", "#10b981"
    elif score >= 75:
        return "👍 Très bien !", "#22c55e"
    elif score >= 60:
        return "😊 Bon travail", "#84cc16"
    elif score >= 50:
        return "🙂 Pas mal", "#eab308"
    elif score >= 40:
        return "🤔 Peut mieux faire", "#f59e0b"
    elif score >= 25:
        return "😕 Continue tes efforts", "#f97316"
    else:
        return "😞 À revoir", "#ef4444"

def create_advanced_score_chart(score):
    """Créer un graphique de score circulaire avancé"""
    fig = go.Figure()
    
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "SCORE FINAL", 'font': {'size': 20}},
        number={'font': {'size': 36}},
        delta={'reference': 50, 'increasing': {'color': "#10b981"}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1},
            'bar': {'color': "#2563eb"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(239, 68, 68, 0.1)'},
                {'range': [50, 75], 'color': 'rgba(234, 179, 8, 0.1)'},
                {'range': [75, 100], 'color': 'rgba(34, 197, 94, 0.1)'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': "Arial"},
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

def create_radar_chart(module_stats):
    """Créer un graphique radar pour les compétences"""
    if len(module_stats) < 3:
        return None
        
    categories = [stat['module'] for stat in module_stats]
    scores = [stat['score'] for stat in module_stats]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(37, 99, 235, 0.2)',
        line=dict(color='#2563eb', width=2),
        name='Compétences'
    ))
    
    fig.update_layout(
        polar=dict(
            bgcolor='white',
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=False,
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig

def create_animated_bar_chart(module_stats):
    """Créer un diagramme en barres animé"""
    df = pd.DataFrame(module_stats)
    
    fig = px.bar(
        df, 
        x='score', 
        y='module',
        orientation='h',
        title='Performance par Module',
        labels={'score': 'Score (%)', 'module': 'Module'},
        color='score',
        color_continuous_scale=['#ef4444', '#eab308', '#10b981'],
        range_color=[0, 100]
    )
    
    fig.update_traces(
        hovertemplate='<b>%{y}</b><br>Score: %{x:.1f}%<br>Questions: %{customdata}',
        customdata=df['count']
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(range=[0, 100]),
        height=350,
        showlegend=False,
        coloraxis_showscale=False
    )
    
    return fig

def create_time_series_chart(questions, results):
    """Créer un graphique de progression pendant le quiz"""
    scores = []
    cumulative = 0
    
    for i, r in enumerate(results['per_question']):
        cumulative += r['score'] * 100
        scores.append(cumulative / (i + 1))
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=list(range(1, len(scores) + 1)),
        y=scores,
        mode='lines+markers',
        line=dict(color='#2563eb', width=3),
        marker=dict(size=6, color='#2563eb'),
        name='Score moyen'
    ))
    
    fig.update_layout(
        title="Progression pendant le quiz",
        xaxis_title="Question",
        yaxis_title="Score moyen (%)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(range=[0, 100]),
        height=250
    )
    
    return fig

def create_history_chart(quiz_history):
    """Créer un graphique de l'historique des scores"""
    if len(quiz_history) < 2:
        return None
    
    df = pd.DataFrame([
        {
            'Quiz': i+1,
            'Score': quiz['total_score'],
            'Date': datetime.fromisoformat(quiz['timestamp']).strftime('%H:%M'),
            'Questions': quiz['n_questions']
        }
        for i, quiz in enumerate(quiz_history[-10:])  # Derniers 10 quiz
    ])
    
    fig = px.line(
        df, 
        x='Quiz', 
        y='Score',
        title='Évolution des Scores',
        markers=True,
        labels={'Score': 'Score (%)', 'Quiz': 'Numéro du Quiz'}
    )
    
    fig.update_traces(
        line=dict(color='#2563eb', width=3),
        marker=dict(size=8, color='#2563eb')
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(range=[0, 100]),
        height=300,
        showlegend=False
    )
    
    return fig

def display_question_review(question_index, question, user_answers, results):
    """Afficher le détail d'une question avec les bonnes réponses et les réponses utilisateur"""
    user_selected = user_answers.get(question_index, [])
    correct_answers = results['per_question'][question_index]['correct']
    
    st.markdown(f"### Question {question_index + 1}")
    st.markdown(f"**{question}**")
    
    # Afficher toutes les options avec leur statut
    for i, choice in enumerate(question.choices):
        col1, col2 = st.columns([1, 20])
        
        with col1:
            if choice in correct_answers and choice in user_selected:
                st.success("✅")
            elif choice in correct_answers:
                st.info("✅")
            elif choice in user_selected:
                st.error("❌")
            else:
                st.write("○")
        
        with col2:
            if choice in correct_answers and choice in user_selected:
                st.markdown(f"<div style='background: rgba(16, 185, 129, 0.1); padding: 1rem; border-radius: 10px; border: 2px solid #10b981; color: #065f46;'><strong>{choice}</strong> ✓ Bonne réponse sélectionnée</div>", unsafe_allow_html=True)
            elif choice in correct_answers:
                st.markdown(f"<div style='background: rgba(59, 130, 246, 0.1); padding: 1rem; border-radius: 10px; border: 2px solid #3b82f6; color: #1e40af;'><strong>{choice}</strong> ✓ Bonne réponse</div>", unsafe_allow_html=True)
            elif choice in user_selected:
                st.markdown(f"<div style='background: rgba(239, 68, 68, 0.1); padding: 1rem; border-radius: 10px; border: 2px solid #ef4444; color: #991b1b;'><strong>{choice}</strong> ✗ Ta réponse</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='padding: 1rem; border-radius: 10px; border: 1px solid #e2e8f0; color: #64748b;'>{choice}</div>", unsafe_allow_html=True)
    
    # Score pour cette question
    question_score = results['per_question'][question_index]['score'] * 100
    score_color = "#10b981" if question_score >= 50 else "#ef4444"
    st.markdown(f"**Score pour cette question :** <span style='color: {score_color}; font-weight: bold;'>{question_score:.0f}%</span>", unsafe_allow_html=True)
    
    st.markdown("---")

def display_history_quiz_details(quiz_index):
    """Afficher le détail d'un quiz de l'historique avec les questions corrigées"""
    if quiz_index is None or quiz_index >= len(st.session_state.quiz_history):
        return
    
    quiz = st.session_state.quiz_history[quiz_index]
    
    # En-tête du quiz historique
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### 📋 Quiz du {datetime.fromisoformat(quiz['timestamp']).strftime('%d/%m/%Y à %H:%M')}")
    with col2:
        score_color = "#10b981" if quiz['total_score'] >= 50 else "#ef4444"
        st.markdown(f"<div style='text-align: center; padding: 0.5rem; background: {score_color}; color: white; border-radius: 10px; font-weight: bold;'>{quiz['total_score']:.1f}%</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div style='text-align: center; padding: 0.5rem; background: #3b82f6; color: white; border-radius: 10px; font-weight: bold;'>{quiz['n_questions']} questions</div>", unsafe_allow_html=True)
    
    st.markdown(f"**Thèmes :** {', '.join(quiz['tags']) if quiz['tags'] else 'Général'}")
    
    # Bouton retour
    if st.button("← Retour à l'historique"):
        st.session_state.viewing_history_quiz = None
        st.rerun()
    
    st.markdown("---")
    
    # Afficher les questions corrigées
    st.markdown("### 📝 Questions Corrigées")
    
    for i, q_result in enumerate(quiz['details']['per_question']):
        with st.expander(f"Question {i+1} - Score: {q_result['score']*100:.0f}%", expanded=False):
            st.markdown(f"**{q_result['question']}**")
            
            # Affichage des réponses
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### ✅ Réponses correctes")
                for answer in q_result['correct']:
                    st.markdown(f"- {answer}")
            
            with col2:
                st.markdown("##### 🎯 Tes réponses")
                for answer in q_result['selected']:
                    if answer in q_result['correct']:
                        st.markdown(f"- ✅ {answer}")
                    else:
                        st.markdown(f"- ❌ {answer}")
            
            # Score de la question
            q_score = q_result['score'] * 100
            score_color = "#10b981" if q_score >= 50 else "#ef4444"
            st.markdown(f"**Score :** <span style='color: {score_color}; font-weight: bold;'>{q_score:.0f}%</span>", unsafe_allow_html=True)

def display_quiz_history():
    """Afficher l'historique détaillé des quiz"""
    if not st.session_state.quiz_history:
        st.info("📝 Aucun quiz dans l'historique pour le moment.")
        return
    
    st.markdown("### 📊 Historique des Quiz")
    
    # Graphique d'évolution des scores
    history_chart = create_history_chart(st.session_state.quiz_history)
    if history_chart:
        st.plotly_chart(history_chart, use_container_width=True)
    
    # Détails de chaque quiz
    for i, quiz in enumerate(reversed(st.session_state.quiz_history[-5:])):  # 5 derniers quiz
        actual_index = len(st.session_state.quiz_history) - 1 - i
        with st.container():
            date_obj = datetime.fromisoformat(quiz['timestamp'])
            formatted_date = date_obj.strftime("%d/%m/%Y à %H:%M")
            
            score_color = "#10b981" if quiz['total_score'] >= 50 else "#ef4444"
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div class='history-card'>
                    <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;'>
                        <div>
                            <h4 style='margin: 0; color: #1e293b;'>🎯 Quiz {len(st.session_state.quiz_history) - i}</h4>
                            <p style='color: #64748b; margin: 0.5rem 0 0 0; font-size: 0.9rem;'>{formatted_date}</p>
                        </div>
                        <div style='text-align: right;'>
                            <div class='result-badge' style='background: {score_color};'>{quiz['total_score']:.1f}%</div>
                            <p style='color: #64748b; margin: 0.5rem 0 0 0; font-size: 0.9rem;'>{quiz['n_questions']} questions</p>
                        </div>
                    </div>
                    <div style='color: #64748b;'>
                        <p><strong>Thèmes :</strong> {', '.join(quiz['tags']) if quiz['tags'] else 'Général'}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("📖 Voir le détail", key=f"view_quiz_{actual_index}", use_container_width=True):
                    st.session_state.viewing_history_quiz = actual_index
                    st.rerun()

# --- Application principale ---
def main():
    """Fonction principale de l'application"""
    
    # Vérifier si on est en mode visualisation d'historique
    if st.session_state.get('viewing_history_quiz') is not None:
        display_history_quiz_details(st.session_state.viewing_history_quiz)
        return
    
    # Utilisation de la classe QuizView pour le rendu de la sidebar
    quiz_view.render_sidebar()
    
    if st.session_state.quiz_finished:
        # --- AFFICHAGE DES RÉSULTATS ---
        results = st.session_state.results
        module_stats = st.session_state.module_stats
        
        st.markdown("<h1 class='main-header'>🎉 Résultats du Quiz</h1>", unsafe_allow_html=True)
        
        # Score final avec graphiques
        col1, col2 = st.columns([1, 2])
        
        with col1:
            fig_gauge = create_advanced_score_chart(results['total_score'])
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            radar_chart = create_radar_chart(module_stats)
            if radar_chart:
                st.plotly_chart(radar_chart, use_container_width=True)
        
        with col2:
            # Feedback général
            feedback, color = get_feedback(results['total_score'])
            st.markdown(f"""
            <div style='
                background: linear-gradient(135deg, {color}15, {color}08);
                border: 2px solid {color};
                border-radius: 20px;
                padding: 2.5rem;
                text-align: center;
                margin: 1rem 0;
            '>
                <h2 style='margin: 0; color: {color}; font-size: 2.2rem;'>{feedback}</h2>
                <p style='font-size: 1.3rem; margin: 1.5rem 0 0 0; color: #1e293b;'>
                    Tu as obtenu <strong style='color: {color};'>{results['total_score']:.1f}%</strong> de bonnes réponses !
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            progress_chart = create_time_series_chart(st.session_state.quiz_questions, results)
            st.plotly_chart(progress_chart, use_container_width=True)
        
        # Diagramme en barres par module
        st.markdown("### 📊 Performance par Thème")
        if len(module_stats) > 1:
            fig_bars = create_animated_bar_chart(module_stats)
            st.plotly_chart(fig_bars, use_container_width=True)
        else:
            st.info("📝 Pas assez de données pour afficher les statistiques par thème.")
        
        # AJOUT: Affichage de l'historique
        display_quiz_history()
        
        # Statistiques détaillées par module
        st.markdown("### 🎯 Analyse par Compétence")
        cols = st.columns(2)
        
        for i, stat in enumerate(module_stats):
            col = cols[i % 2]
            feedback_text, color = get_feedback(stat['score'])
            
            with col:
                st.markdown(f"""
                <div class='stats-card'>
                    <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;'>
                        <h4 style='margin: 0; color: #1e293b;'>📚 {stat['module']}</h4>
                        <div class='result-badge' style='background: {color};'>{stat['score']:.1f}%</div>
                    </div>
                    <div style='color: #64748b;'>
                        <p><strong>Questions traitées:</strong> {stat['count']}</p>
                        <p><strong>Niveau:</strong> {feedback_text}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Détails question par question
        st.markdown("### 📝 Détail des Réponses")
        
        # Vérifier que nous avons les données nécessaires
        if hasattr(st.session_state, 'quiz_questions') and hasattr(st.session_state, 'user_answers'):
            for i, question in enumerate(st.session_state.quiz_questions):
                display_question_review(i, question, st.session_state.user_answers, results)
        else:
            # Fallback vers l'ancienne méthode si les nouvelles données ne sont pas disponibles
            for r in results["per_question"]:
                with st.container():
                    score_color = "#10b981" if r['score'] >= 0.5 else "#ef4444"
                    question_feedback, _ = get_feedback(r['score'] * 100)
                    emoji = "✅" if r['score'] >= 0.5 else "❌"
                    
                    st.markdown(f"""
                    <div class='stats-card'>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;'>
                            <h4 style='margin: 0; color: #1e293b;'>{emoji} Question {r['index']+1}</h4>
                            <span style='color: {score_color}; font-weight: bold;'>{question_feedback}</span>
                        </div>
                        <p style='color: #1e293b; font-size: 1.1rem; margin-bottom: 1.5rem;'><strong>{r['question']}</strong></p>
                        
                        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;'>
                            <div style='background: rgba(16, 185, 129, 0.1); padding: 1rem; border-radius: 10px; border: 1px solid rgba(16, 185, 129, 0.3);'>
                                <p style='margin: 0; color: #10b981; font-weight: bold;'>✅ Réponses correctes</p>
                                <p style='margin: 0.5rem 0 0 0; color: #1e293b;'>{', '.join(r['correct']) if r['correct'] else 'Aucune'}</p>
                            </div>
                            <div style='background: rgba(37, 99, 235, 0.1); padding: 1rem; border-radius: 10px; border: 1px solid rgba(37, 99, 235, 0.3);'>
                                <p style='margin: 0; color: #2563eb; font-weight: bold;'>🎯 Tes réponses</p>
                                <p style='margin: 0.5rem 0 0 0; color: #1e293b;'>{', '.join(r['selected']) if r['selected'] else 'Aucune sélection'}</p>
                            </div>
                        </div>
                        
                        <div style='margin-top: 1.5rem; text-align: center;'>
                            <span style='color: {score_color}; font-weight: bold; font-size: 1.1rem;'>Score: {r['score']*100:.0f}%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Bouton pour recommencer
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Recommencer le quiz", use_container_width=True, type="primary"):
                quiz_view.reset_quiz()
                st.rerun()

    elif st.session_state.quiz_generated and st.session_state.quiz is not None:
        # --- AFFICHAGE DU QUIZ EN COURS ---
        questions = st.session_state.quiz
        q_index = st.session_state.step
        
        if not isinstance(q_index, int) or q_index < 0 or q_index >= len(questions):
            st.error("Erreur: Index de question invalide. Réinitialisation du quiz.")
            quiz_view.initialize_quiz([], 10)
            st.rerun()
        else:
            current_q = questions[q_index]
            
            # AJOUT: Utilisation de la classe QuizView pour le rendu
            quiz_view.render_question(current_q, q_index, len(questions))
            quiz_view.render_navigation(q_index, len(questions))

    else:
        # --- ÉCRAN D'ACCUEIL ---
        st.markdown("<h1 class='main-header'>🧠 Quiz Interactif</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-header'>Testez vos connaissances avec notre plateforme de quiz interactive et moderne</p>", unsafe_allow_html=True)
        
        # Cartes de fonctionnalités
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class='stats-card' style='text-align: center;'>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>🎯</div>
                <h3 style='color: #1e293b;'>Quiz Personnalisés</h3>
                <p style='color: #64748b;'>Choisissez les thèmes et le nombre de questions selon vos besoins</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class='stats-card' style='text-align: center;'>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>📊</div>
                <h3 style='color: #1e293b;'>Analyses Détaillées</h3>
                <p style='color: #64748b;'>Obtenez des statistiques complètes sur vos performances</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class='stats-card' style='text-align: center;'>
                <div style='font-size: 2.5rem; margin-bottom: 1rem;'>⚡</div>
                <h3 style='color: #1e293b;'>Interface Moderne</h3>
                <p style='color: #64748b;'>Expérience utilisateur fluide et design élégant</p>
            </div>
            """, unsafe_allow_html=True)
        
        # AJOUT: Affichage de l'historique sur la page d'accueil si des quiz ont été complétés
        if st.session_state.quiz_history:
            st.markdown("### 📈 Tes Progrès")
            display_quiz_history()
        
        # Message d'instruction
        st.info("""
        **🎮 Pour commencer :** 
        - Configurez votre quiz dans la barre latérale 
        - Sélectionnez les thèmes qui vous intéressent
        - Choisissez le nombre de questions
        - Cliquez sur **'Générer le quiz'** pour démarrer !
        """)

if __name__ == "__main__":
    main()