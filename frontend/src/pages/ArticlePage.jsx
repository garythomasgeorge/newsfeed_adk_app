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
            <div style={{
                backgroundColor: '#fff',
                padding: '30px',
                borderRadius: '16px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                border: '1px solid #e9ecef'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '25px' }}>
                    <span style={{ fontSize: '1.5rem' }}>📋</span>
                    <h3 style={{ margin: 0, fontSize: '1.2rem', color: '#333', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '700' }}>Detailed Analysis</h3>
                </div>
                {sections.map((section, idx) => (
                    <div key={idx} style={{
                        marginBottom: idx < sections.length - 1 ? '25px' : 0,
                        paddingBottom: idx < sections.length - 1 ? '25px' : 0,
                        borderBottom: idx < sections.length - 1 ? '1px solid #e9ecef' : 'none'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                            <span style={{ fontSize: '1.2rem' }}>{sectionIcons[section.title] || '•'}</span>
                            <h4 style={{ margin: 0, fontSize: '1.05rem', fontWeight: '600', color: '#333' }}>{section.title}</h4>
                        </div>
                        <p style={{ margin: 0, lineHeight: '1.7', color: '#555', fontSize: '1rem' }}>
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
        <div style={{ maxWidth: '800px', margin: '0 auto', padding: '40px 20px', fontFamily: 'Inter, sans-serif' }}>
            {/* ... (existing back button and header) */}
            <button
                onClick={() => navigate('/')}
                style={{
                    background: 'none',
                    border: 'none',
                    color: '#666',
                    cursor: 'pointer',
                    fontSize: '1rem',
                    marginBottom: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px'
                }}
            >
                ← Back to Feed
            </button>

            <header style={{ marginBottom: '30px' }}>
                <div style={{ display: 'flex', gap: '10px', marginBottom: '15px', flexWrap: 'wrap' }}>
                    <BiasMeter bias={article.bias_label} />
                    <span style={{ color: '#888' }}>{new Date(article.created_at).toLocaleDateString()}</span>
                    {article.category && (
                        <span style={{
                            backgroundColor: '#e3f2fd',
                            color: '#1976d2',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '0.9rem'
                        }}>
                            {article.category}
                        </span>
                    )}
                </div>

                <h1 style={{ fontSize: '3rem', fontWeight: '800', lineHeight: '1.2', marginBottom: '20px', color: '#1a1a1a' }}>
                    {article.headline}
                </h1>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {article.topic_tags && article.topic_tags.map(tag => (
                        <span key={tag} style={{
                            backgroundColor: '#f5f5f5',
                            padding: '6px 12px',
                            borderRadius: '20px',
                            fontSize: '0.85rem',
                            color: '#555',
                            fontWeight: '500'
                        }}>
                            #{tag}
                        </span>
                    ))}
                </div>
            </header>

            {/* TL;DR Card */}
            <div style={{
                backgroundColor: '#fff',
                padding: '30px',
                borderRadius: '16px',
                marginBottom: '30px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                border: '1px solid #e9ecef'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                    <span style={{ fontSize: '1.5rem' }}>⚡</span>
                    <h3 style={{ margin: 0, fontSize: '1.2rem', color: '#333', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: '700' }}>TL;DR</h3>
                </div>
                <p style={{ fontSize: '1.1rem', lineHeight: '1.7', margin: 0, color: '#444' }}>
                    {article.tldr_summary || article.summary}
                </p>
            </div>

            {/* Detailed Summary Card */}
            {renderDetailedSummary(article.detailed_summary)}

            {/* View Other Sources Section */}
            <div style={{
                marginTop: '40px',
                backgroundColor: '#fff',
                padding: '30px',
                borderRadius: '16px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                border: '1px solid #e9ecef'
            }}>
                <button
                    onClick={handleViewOtherSources}
                    style={{
                        backgroundColor: showSimilar ? '#f8f9fa' : '#007bff',
                        color: showSimilar ? '#333' : '#fff',
                        border: 'none',
                        padding: '14px 28px',
                        borderRadius: '10px',
                        fontSize: '1.05rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        marginBottom: showSimilar ? '25px' : 0,
                        transition: 'all 0.2s',
                        boxShadow: showSimilar ? 'none' : '0 2px 4px rgba(0,123,255,0.2)'
                    }}
                    onMouseEnter={(e) => {
                        if (!showSimilar) {
                            e.currentTarget.style.backgroundColor = '#0056b3';
                            e.currentTarget.style.transform = 'translateY(-1px)';
                        }
                    }}
                    onMouseLeave={(e) => {
                        if (!showSimilar) {
                            e.currentTarget.style.backgroundColor = '#007bff';
                            e.currentTarget.style.transform = 'translateY(0)';
                        }
                    }}
                >
                    <span style={{ fontSize: '1.2rem' }}>🔍</span>
                    {showSimilar ? 'Hide Other Sources' : 'View Other Sources'}
                </button>

                {showSimilar && (
                    <div style={{ animation: 'fadeIn 0.3s ease-in' }}>
                        {loadingSimilar ? (
                            <p style={{ color: '#666', fontStyle: 'italic' }}>Finding related articles...</p>
                        ) : similarArticles.length > 0 ? (
                            <div style={{ display: 'grid', gap: '15px' }}>
                                {similarArticles.map(sim => (
                                    <div key={sim.url}
                                        onClick={() => navigate('/article', { state: { article: sim } })}
                                        style={{
                                            border: '1px solid #e9ecef',
                                            borderRadius: '12px',
                                            padding: '18px',
                                            cursor: 'pointer',
                                            backgroundColor: '#fafbfc',
                                            transition: 'all 0.2s',
                                        }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.transform = 'translateY(-2px)';
                                            e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                                            e.currentTarget.style.backgroundColor = '#fff';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.transform = 'translateY(0)';
                                            e.currentTarget.style.boxShadow = 'none';
                                            e.currentTarget.style.backgroundColor = '#fafbfc';
                                        }}
                                    >
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', alignItems: 'center' }}>
                                            <BiasMeter bias={sim.bias_label} />
                                            <span style={{ fontSize: '0.8rem', color: '#888', fontWeight: '500' }}>
                                                {new URL(sim.url).hostname.replace('www.', '')}
                                            </span>
                                        </div>
                                        <h4 style={{ margin: '5px 0 0 0', fontSize: '1.05rem', fontWeight: '600', color: '#333', lineHeight: '1.4' }}>{sim.headline}</h4>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p style={{ color: '#666', textAlign: 'center', padding: '20px 0' }}>No similar articles found in our database.</p>
                        )}
                    </div>
                )}
            </div>

            <div style={{ marginTop: '30px', textAlign: 'center' }}>
                <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                        display: 'inline-block',
                        backgroundColor: '#000',
                        color: 'white',
                        padding: '16px 32px',
                        borderRadius: '30px',
                        textDecoration: 'none',
                        fontWeight: '600',
                        fontSize: '1.1rem',
                        transition: 'transform 0.2s'
                    }}
                >
                    Read Original Article
                </a>
            </div>
        </div>
    );
};

export default ArticlePage;
