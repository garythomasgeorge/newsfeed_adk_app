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

    // Helper to render markdown-like sections if we don't have a library
    const renderDetailedSummary = (text) => {
        if (!text) return <p>No detailed summary available.</p>;

        // Simple split by double newlines to create paragraphs
        return text.split('\n').map((line, index) => {
            if (line.trim().startsWith('**') && line.trim().endsWith('**')) {
                return <h3 key={index} style={{ marginTop: '20px', marginBottom: '10px' }}>{line.replace(/\*\*/g, '')}</h3>;
            }
            if (line.trim().startsWith('**')) {
                // Handle inline bolding for section headers like "**What Happened**: ..."
                const parts = line.split('**:');
                if (parts.length > 1) {
                    return <p key={index} style={{ marginBottom: '15px', lineHeight: '1.6' }}><strong>{parts[0].replace(/\*\*/g, '')}:</strong>{parts.slice(1).join('**:')}</p>;
                }
            }
            return <p key={index} style={{ marginBottom: '15px', lineHeight: '1.6' }}>{line}</p>;
        });
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

                <h1 style={{ fontSize: '2.5rem', fontWeight: '800', lineHeight: '1.2', marginBottom: '20px' }}>
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

            <div style={{ backgroundColor: '#fafafa', padding: '25px', borderRadius: '12px', marginBottom: '40px', borderLeft: '4px solid #007bff' }}>
                <h3 style={{ marginTop: 0, fontSize: '1.1rem', color: '#333', textTransform: 'uppercase', letterSpacing: '0.05em' }}>TL;DR</h3>
                <p style={{ fontSize: '1.1rem', lineHeight: '1.6', margin: 0 }}>
                    {article.tldr_summary || article.summary}
                </p>
            </div>

            <div style={{ fontSize: '1.1rem', color: '#333' }}>
                {renderDetailedSummary(article.detailed_summary)}
            </div>

            {/* View Other Sources Section */}
            <div style={{ marginTop: '40px', borderTop: '1px solid #eee', paddingTop: '30px' }}>
                <button
                    onClick={handleViewOtherSources}
                    style={{
                        backgroundColor: '#f0f0f0',
                        border: 'none',
                        padding: '12px 24px',
                        borderRadius: '8px',
                        fontSize: '1rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        marginBottom: '20px'
                    }}
                >
                    {showSimilar ? 'Hide Other Sources' : 'View Other Sources'}
                    <span style={{ fontSize: '0.8rem', color: '#666' }}>Find similar coverage</span>
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
                                            border: '1px solid #eee',
                                            borderRadius: '8px',
                                            padding: '15px',
                                            cursor: 'pointer',
                                            backgroundColor: '#fff',
                                            transition: 'transform 0.2s',
                                            ':hover': { transform: 'translateY(-2px)' }
                                        }}
                                    >
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                                            <BiasMeter bias={sim.bias_label} />
                                            <span style={{ fontSize: '0.8rem', color: '#888' }}>
                                                {new URL(sim.url).hostname.replace('www.', '')}
                                            </span>
                                        </div>
                                        <h4 style={{ margin: '5px 0', fontSize: '1.1rem' }}>{sim.headline}</h4>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p style={{ color: '#666' }}>No similar articles found in our database.</p>
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
