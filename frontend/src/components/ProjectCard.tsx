import React from 'react';
import { ArrowRight } from 'lucide-react';

interface ProjectCardProps {
    title: string;
    description: string;
    image?: string;
    tags: string[];
    onClick: () => void;
}

export const ProjectCard: React.FC<ProjectCardProps> = ({ title, description, image, tags, onClick }) => {
    return (
        <div
            className="group relative overflow-hidden rounded-2xl bg-white/5 p-6 transition-all hover:bg-white/10 hover:shadow-2xl hover:shadow-purple-500/20 border border-white/10 backdrop-blur-sm cursor-pointer"
            onClick={onClick}
        >
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-blue-500/10 opacity-0 group-hover:opacity-100 transition-opacity" />

            <div className="relative z-10">
                <div className="mb-4 h-40 w-full rounded-xl bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center overflow-hidden">
                    {image ? (
                        <img src={image} alt={title} className="w-full h-full object-cover opacity-80 group-hover:scale-105 transition-transform duration-500" />
                    ) : (
                        <div className="text-4xl">🚀</div>
                    )}
                </div>

                <h3 className="text-xl font-bold text-white mb-2 group-hover:text-purple-400 transition-colors">{title}</h3>
                <p className="text-gray-400 text-sm mb-4 line-clamp-2">{description}</p>

                <div className="flex flex-wrap gap-2 mb-4">
                    {tags.map((tag, index) => (
                        <span key={index} className="px-2 py-1 text-xs rounded-full bg-white/5 text-gray-300 border border-white/10">
                            {tag}
                        </span>
                    ))}
                </div>

                <div className="flex items-center text-sm font-medium text-purple-400 group-hover:translate-x-1 transition-transform">
                    Tester le projet <ArrowRight className="ml-1 w-4 h-4" />
                </div>
            </div>
        </div>
    );
};
