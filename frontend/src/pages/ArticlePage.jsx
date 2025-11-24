import React from 'react';
import axios from 'axios';
import { useLocation, useNavigate } from 'react-router-dom';
import BiasMeter from '../components/BiasMeter';
import ReactMarkdown from 'react-markdown'; // We might need to install this, or just render as text for now

const ArticlePage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const article = location.state?.article;

    if (!article) {
        return (
            <div style={{ padding: '40px', textAlign: 'center' }}>
                <p>Article not found. <button onClick={() => navigate('/')}>Go Home</button></p>
            </div>
        );
    }

    // Helper to render markdown-like sections with card-based design
    const renderDetailedSummary = (text) => {
        if (!text) return <p>No detailed summary available.</p>;

        const sections = [];
        const lines = text.split('\n');
        let currentSection = null;
        let currentContent = [];

        const sectionIcons = {
            'What Happened': '📰',
            'Impact': '💥',
            'Reactions': '💬',
            'Conclusion': '🎯'
        };

        lines.forEach((line, index) => {
            if (line.trim().startsWith('**') && line.includes(':')) {
                // Save previous section
                if (currentSection) {
                    sections.push({
                        title: currentSection,
                        content: currentContent.join(' ')
                    });
                }
                // Start new section
                const titleMatch = line.match(/\*\*(.+?)\*\*:/);
                if (titleMatch) {
                    currentSection = titleMatch[1];
                    currentContent = [line.split('**:')[1]];
                }
            } else if (line.trim()) {
                currentContent.push(line);
            }
        });

        // Add last section
        if (currentSection) {
            sections.push({
                title: currentSection,
                content: currentContent.join(' ')
            });
        }

        return (
            <div className="article-card detailed-analysis-card">
                <div className="card-header">
                    <span className="card-icon">📋</span>
                    <h3>Detailed Analysis</h3>
                </div>
                {sections.map((section, idx) => (
                    <div key={idx} className="analysis-section">
                        <div className="section-header">
                            <span className="section-icon">{sectionIcons[section.title] || '•'}</span>
                            <h4>{section.title}</h4>
                        </div>
                        <p>
                            {section.content}
                        </p>
                    </div>
                ))}
            </div>
        );
    };

    const [similarArticles, setSimilarArticles] = React.useState([]);
    const [loadingSimilar, setLoadingSimilar] = React.useState(false);
    const [showSimilar, setShowSimilar] = React.useState(false);

    // Use relative path to leverage Vite proxy
    const API_BASE_URL = '/api';

    // ... (existing helper functions)

    const handleViewOtherSources = async () => {
        if (showSimilar) {
            setShowSimilar(false);
            return;
        }

        setShowSimilar(true);
        if (similarArticles.length > 0) return; // Already fetched

        setLoadingSimilar(true);
        try {
            // Use encodeURIComponent for the URL parameter
            const response = await axios.get(`${API_BASE_URL}/articles/similar?url=${encodeURIComponent(article.url)}`);
            setSimilarArticles(response.data);
        } catch (error) {
            console.error("Error fetching similar articles:", error);
        }
        setLoadingSimilar(false);
    };

    return (
        <div className="article-container">
            <button
                onClick={() => navigate('/')}
                className="back-button"
            >
                ← Back to Feed
            </button>

            <header className="article-header">
                <div className="article-meta">
                    <BiasMeter bias={article.bias_label} />
                    <span className="article-date">{new Date(article.created_at).toLocaleDateString()}</span>
                    {article.category && (
                        <span className="article-category">
                            {article.category}
                        </span>
                    )}
                </div>

                <h1 className="article-title">
                    {article.headline}
                </h1>

                <div className="article-tags">
                    {article.topic_tags && article.topic_tags.map(tag => (
                        <span key={tag} className="article-tag">
                            #{tag}
                        </span>
                    ))}
                </div>
            </header>

            {/* TL;DR Card */}
            <div className="article-card tldr-card">
                <div className="card-header">
                    <span className="card-icon">⚡</span>
                    <h3>TL;DR</h3>
                </div>
                <p>
                    {article.tldr_summary || article.summary}
                </p>
            </div>

            {/* Detailed Summary Card */}
            {renderDetailedSummary(article.detailed_summary)}

            {/* View Other Sources Section */}
            <div className="article-card similar-sources-card">
                <button
                    onClick={handleViewOtherSources}
                    className={`view-sources-btn ${showSimilar ? 'active' : ''}`}
                >
                    <span className="btn-icon">🔍</span>
                    {showSimilar ? 'Hide Other Sources' : 'View Other Sources'}
                </button>

                {showSimilar && (
                    <div className="similar-articles-container">
                        {loadingSimilar ? (
                            <p className="loading-text">Finding related articles...</p>
                        ) : similarArticles.length > 0 ? (
                            <div className="similar-articles-grid">
                                {similarArticles.map(sim => (
                                    <div key={sim.url}
                                        onClick={() => navigate('/article', { state: { article: sim } })}
                                        className="similar-article-item"
                                    >
                                        <div className="similar-article-meta">
                                            <BiasMeter bias={sim.bias_label} />
                                            <span className="similar-article-source">
                                                {new URL(sim.url).hostname.replace('www.', '')}
                                            </span>
                                        </div>
                                        <h4>{sim.headline}</h4>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="no-results-text">No similar articles found in our database.</p>
                        )}
                    </div>
                )}
            </div>

            <div className="read-original-container">
                <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="read-original-btn"
                >
                    Read Original Article
                </a>
            </div>
        </div>
    );
};

export default ArticlePage;
