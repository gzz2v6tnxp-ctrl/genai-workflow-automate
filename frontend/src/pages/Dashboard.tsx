import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ProjectCard } from '../components/ProjectCard';
import { Layout } from '../components/Layout';
import { Sparkles, LayoutGrid } from 'lucide-react';

export const Dashboard: React.FC = () => {
    const navigate = useNavigate();

    const projects = [
        {
            id: 'genai-workflow',
            title: 'GenAI Workflow Automate - Gestion des tickets utilisateurs',
            description: 'Gestion des tickets utilisateurs avec une interface conversationnelle intuitive.',
            tags: ['AI Agent', 'Langgraph', 'Workflow', 'Automation', 'Multisources', 'NLP', 'QDrant', 'Embeddings', 'Vector database', 'CI/CD', 'LLM', 'RAG', 'FinTech'],
            path: '/project/genai-workflow'
        },
        {
            id: 'mlops-pipeline-orchestrator',
            title: 'Projet Machine Learning & MLOps Pipeline Orchestrator (En cours)',
            description: 'MLOps Pipeline Orchestrator End-to-end machine learning pipeline automation using Airflow and Kubernetes. Automated training, evaluation, and deployment of models.',
            tags: ['Machine Learning', 'Data Cleaning', 'Data Preprocessing', 'Data Visualization', 'MLOps', 'CI/CD', 'Airflow', 'Kubernetes', 'DAG', 'FinTech'],
            path: '#'
        },
        {
            id: 'lead-generation-audit-energetique',
            title: 'Génération des leads (Next)',
            description: 'Génération des leads pour l\'audit énergétique assistée par IA.',
            tags: ['Automatisation', 'n8n', 'Hubspot', 'LLM', 'QDrant', 'Embeddings', 'Vector database', 'CI/CD', 'LLM', 'RAG', 'Audit Energetique'],
            path: '#'
        }
    ];

    return (
        <Layout>
            <div className="max-w-7xl mx-auto px-6 py-12">
                {/* Header */}
                <header className="flex items-center justify-between mb-20">
                    <div className="flex items-center gap-2">
                        <div className="p-2 bg-white/5 rounded-lg border border-white/10">
                            <LayoutGrid className="w-6 h-6 text-purple-400" />
                        </div>
                        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                            Project Banquet
                        </span>
                    </div>
                    <div className="flex items-center gap-4">
                        <button className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors">
                            Documentation
                        </button>
                        <a
                            href="https://www.linkedin.com/in/sitraka-l-ravelojaona"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-4 py-2 text-sm font-medium bg-white text-black rounded-lg hover:bg-gray-200 transition-colors"
                        >
                            Contact
                        </a>
                    </div>
                </header>

                {/* Hero Section */}
                <div className="text-center mb-24">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-6 animate-fade-in">
                        <Sparkles className="w-4 h-4 text-yellow-400" />
                        <span className="text-sm text-gray-300">Découvrez mes dernières innovations IA</span>
                    </div>
                    <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-b from-white via-white to-gray-500">
                        L'intelligence Artificielle <br /> à portée de main.
                    </h1>
                    <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
                        Explorez ma collection de projets IA expérimentaux et prêts pour la production (MVP).
                        <br /> Testez, itérez et intégrez le futur dès aujourd'hui.
                    </p>
                </div>

                {/* Projects Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {projects.map((project) => (
                        <ProjectCard
                            key={project.id}
                            title={project.title}
                            description={project.description}
                            tags={project.tags}
                            onClick={() => {
                                if (project.path !== '#') {
                                    navigate(project.path);
                                }
                            }}
                        />
                    ))}
                </div>

                {/* Footer */}
                <footer className="mt-32 pt-8 border-t border-white/10 text-center text-gray-500 text-sm">
                    <p>&copy; 2025 Project Banquet. Tous droits réservés.</p>
                </footer>
            </div>
        </Layout>
    );
};
