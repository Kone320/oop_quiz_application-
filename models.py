# models.py
from __future__ import annotations
import json
import random
from pathlib import Path
from typing import List, Dict, Set, Optional

class Question:
    """
    Représente une question unique du quiz.

    Attributs :
      - question : str → le texte de la question
      - choices : List[str] → les choix de réponses proposés
      - correct : List[str] → la ou les bonnes réponses
      - mode : 'single' ou 'multiple' → type de question
      - tags : List[str] → étiquettes thématiques (catégories)
    """
    def __init__(self, question: str, choices: List[str], correct: List[str],
                 mode: str = "single", tags: Optional[List[str]] = None):
        self.question = question
        self.choices = choices
        # Normalisation sous forme de liste
        self.correct = list(correct) if correct is not None else []
        self.mode = mode
        self.tags = tags or []

    def is_single(self) -> bool:
        """Renvoie True si la question est à choix unique."""
        return self.mode == "single"

    def is_multiple(self) -> bool:
        """Renvoie True si la question est à choix multiple."""
        return self.mode == "multiple"

    def is_single_choice(self) -> bool:
        """Renvoie True si la question est à choix unique (alias pour compatibilité README)."""
        return self.is_single()

    def to_dict(self) -> Dict:
        """Convertit la question en dictionnaire (utile pour l'export ou le debug)."""
        return {
            "question": self.question,
            "choices": list(self.choices),
            "correct": list(self.correct),
            "mode": self.mode,
            "tags": list(self.tags)
        }

    def __repr__(self):
        """Affichage lisible pour le débogage."""
        return f"Question({self.question!r}, mode={self.mode}, tags={self.tags})"


class QuestionDataset:
    """
    Classe Singleton pour charger les questions du quiz depuis un fichier JSON.

    Fonctionnalités :
      - Charge les données une seule fois.
      - Convertit les questions JSON en objets `Question`.
      - Fournit les tags disponibles pour filtrer les questions.

    Exemple d'utilisation :
        ds = QuestionDataset("quiz_dataset.json")
    """
    _instance = None

    def __new__(cls, file_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(QuestionDataset, cls).__new__(cls)
            cls._instance.questions = []
            cls._instance.file_path = None
            if file_path:
                cls._instance.load(file_path)
        else:
            if file_path:
                cls._instance.load(file_path)
        return cls._instance

    def load(self, file_path: Optional[str] = None):
        """
        Charge les questions à partir du fichier JSON.
        Si aucun chemin n'est donné, essaie de charger 'quiz_dataset.json' dans le même dossier que ce fichier.
        """
        if file_path is None:
            base = Path(__file__).parent
            file_path = base / "quiz_dataset.json"

        fp = Path(file_path)
        if not fp.exists():
            raise FileNotFoundError(f"Fichier de quiz introuvable à l'emplacement {fp.resolve()}")

        with fp.open("r", encoding="utf-8") as f:
            data = json.load(f)

        questions = []
        for item in data:
            q = Question(
                question=item.get("question", ""),
                choices=item.get("choices", []),
                correct=item.get("correct", []),
                mode=item.get("mode", "single"),
                tags=item.get("tags", [])
            )
            questions.append(q)

        self.questions = questions
        self.file_path = str(fp)
        return self

    def all_tags(self) -> Set[str]:
        """Retourne l'ensemble de tous les tags uniques présents dans le dataset."""
        tags = set()
        for q in self.questions:
            tags.update(q.tags)
        return tags

    def get_questions_by_tags(self, tags: Optional[List[str]] = None) -> List[Question]:
        """
        Retourne la liste des questions correspondant à au moins un des tags fournis.
        Si aucun tag n'est donné, retourne toutes les questions.
        """
        if not tags:
            return list(self.questions)
        tags_set = set(tags)
        filtered = [q for q in self.questions if tags_set.intersection(q.tags)]
        return filtered

    def as_dict_list(self) -> List[Dict]:
        """Retourne toutes les questions sous forme de liste de dictionnaires."""
        return [q.to_dict() for q in self.questions]


class QuizGenerator:
    """
    Génère un quiz à partir du dataset filtré par tags.
    """
    def __init__(self, dataset: QuestionDataset):
        self.dataset = dataset

    def generate(self, tags: Optional[List[str]] = None, n_questions: int = 10, shuffle: bool = True) -> List[Question]:
        """
        Sélectionne aléatoirement un sous-ensemble de questions correspondant aux tags choisis.
        Si le nombre demandé dépasse la taille disponible, retourne toutes les questions correspondantes.
        """
        pool = self.dataset.get_questions_by_tags(tags)
        if not pool:
            return []
        if shuffle:
            random.shuffle(pool)
        selected = pool[:min(n_questions, len(pool))]
        return selected


class QuizCorrector:
    """
    Corrige un quiz et calcule les scores.

    Méthodes principales :
      - score_single : calcule le score pour une question à choix unique.
      - score_multiple : applique la formule proportionnelle pour les choix multiples :
            score = max(0, |correct ∩ selected| / |correct| - |selected - correct| / |correct|)
      - correct_quiz : retourne le score détaillé par question et le total en pourcentage.
    """
    @staticmethod
    def score_single(correct: List[str], selected: List[str]) -> float:
        """
        Logique de score pour les questions à choix unique :
        - 1 point si la réponse sélectionnée est correcte.
        - 0 sinon.
        """
        if not correct:
            return 0.0
        return 1.0 if len(selected) == 1 and selected[0] in correct else 0.0

    @staticmethod
    def score_multiple(correct: List[str], selected: List[str]) -> float:
        """
        Logique de score pour les questions à choix multiple selon la formule du README :
        score = max(0, |correct ∩ selected| / |correct| - |selected - correct| / |correct|)
        
        Formule officielle :
        score = max(0, (nombre de bonnes réponses sélectionnées / total bonnes réponses) 
                      - (nombre de mauvaises réponses sélectionnées / total bonnes réponses))
        """
        correct_set = set(correct)
        selected_set = set(selected or [])
        if not correct_set:
            return 0.0

        # Intersection = bonnes réponses choisies
        intersect = correct_set.intersection(selected_set)
        # Sélections erronées = mauvaises réponses choisies
        false_selected = selected_set - correct_set

        numerator = len(intersect)
        denom = len(correct_set)

        score = (numerator / denom) - (len(false_selected) / denom)
        return max(0.0, score)

    def correct_quiz(self, questions: List[Question], answers: Dict[int, List[str]]) -> Dict:
        """
        Corrige l'ensemble du quiz et calcule les scores.

        Paramètres :
          - questions : liste d'objets Question (dans l'ordre)
          - answers : dictionnaire {index_question -> réponses sélectionnées}

        Retourne :
          {
            "per_question": [
              {
                "index": i,
                "score": float (0..1),
                "max_score": 1.0,
                "correct": [...],
                "selected": [...],
                "mode": "single" ou "multiple"
              }
            ],
            "total_score": score total (0..100)
          }
        """
        per_question = []
        total_points = 0.0

        for i, q in enumerate(questions):
            selected = answers.get(i, [])
            if q.is_single():
                s = self.score_single(q.correct, selected)
            else:
                s = self.score_multiple(q.correct, selected)

            per_question.append({
                "index": i,
                "question": q.question,
                "mode": q.mode,
                "correct": list(q.correct),
                "selected": list(selected),
                "score": float(s),
                "max_score": 1.0
            })
            total_points += s

        # Calcul du score total en pourcentage
        if questions:
            total_score_pct = (total_points / len(questions)) * 100.0
        else:
            total_score_pct = 0.0

        return {
            "per_question": per_question,
            "total_score": total_score_pct
        }


# Si ce module est exécuté directement (pour un test rapide)
if __name__ == "__main__":
    ds = QuestionDataset()  # essaie de charger quiz_dataset.json dans le même dossier
    try:
        ds.load()  # chargement explicite
        print(f"{len(ds.questions)} questions chargées, tags disponibles : {sorted(ds.all_tags())[:10]}")
    except Exception as e:
        print("Aucun dataset chargé :", e)