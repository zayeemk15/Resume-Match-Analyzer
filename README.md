# AI Resume Match Analyzer (Production) 🚀

An advanced, production-ready AI Resume Matching engine that computes compatibility scores between resumes and job descriptions using an ensemble of NLP techniques (TF-IDF, SBERT, and BERT).

## 🚀 Key Features
- **Integrated Engine**: Direct logic calls for unified frontend-backend performance.
- **Advanced NLP**: High-precision match scores based on Semantic Similarity.
- **ATS Simulator**: Compliance scoring and keyword feedback.
- **Skill Gap Report**: Targeted identifies missing prioritize-based skills.
- **AI Career Coach**: Personalized resume improvement suggestions.

## 🛠 Tech Stack
- **Dashboard**: Streamlit
- **Intelligence**: Scikit-Learn, Sentence-Transformers, Spacy, PyTorch
- **Extraction**: PDFPlumber, Python-DOCX
- **Persistence**: SQLite (SQLAlchemy)

## 🐳 Deployment (Docker)
Built for easy deployment on **Render** using a single container:

```bash
docker build -t resume-analyzer .
docker run -p 8501:8501 resume-analyzer
```

## 📂 Project Structure
- `app.py`: Streamlit main dashboard.
- `utils/`: Core NLP intelligence and business logic.
- `utils/components/`: Modular UI dashboard sections.
- `utils/db/`: Database models and CRUD.
- `Dockerfile`: Production container config.
- `requirements.txt`: Unified dependency list.

---
**Author:** AI Resume Analyzer by Zayeem khateeb
