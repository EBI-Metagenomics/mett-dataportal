import React, {useState} from 'react';
import {useNavigate} from 'react-router-dom';
import styles from './FeedbackPage.module.scss';
import {ApiService} from '../../services/api';

interface FeedbackFormData {
    name: string;
    email: string;
    cc: string;
    subject: string;
    feedback: string;
}

const FeedbackPage: React.FC = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState<FeedbackFormData>({
        name: '',
        email: '',
        cc: '',
        subject: '',
        feedback: ''
    });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const {name, value} = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        setSubmitStatus('idle');

        try {
            const response = await ApiService.post('/feedback/submit', formData);

            // The new Pydantic response format includes status, message, etc.
            if (response && (response.status === 'success' || response.success)) {
                setSubmitStatus('success');
                setTimeout(() => {
                    navigate('/');
                }, 2000);
            } else {
                setSubmitStatus('error');
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
            setSubmitStatus('error');
        } finally {
            setIsSubmitting(false);
        }
    };

    const isFormValid = formData.name.trim() && formData.email.trim() && formData.subject.trim() && formData.feedback.trim();

    return (
        <div className={styles.feedbackPage}>
            <div className="vf-container">
                {/* Breadcrumb Section */}
                <nav className="vf-breadcrumbs" aria-label="Breadcrumb">
                    <ul className="vf-breadcrumbs__list vf-list vf-list--inline">
                        <li className={styles.breadcrumbsItem}>
                            <a href="/" className="vf-breadcrumbs__link">Home</a>
                        </li>
                        <span className={styles.separator}> | </span>
                        <li className={styles.breadcrumbsItem}>
                            <b>Feedback</b>
                        </li>
                    </ul>
                </nav>

                <div className="vf-section-header">
                    <p/>
                    <h1 className="vf-section-header__heading">Feedback</h1>
                    <p className="vf-section-header__subheading">
                        We value your feedback on the METT Data Portal. Please share your thoughts, suggestions, or
                        report any issues you encounter.
                    </p>
                </div>

                <div className="vf-grid vf-grid__col-3">
                    <div className="vf-grid__col--span-2">
                        <div className="vf-content">
                            {submitStatus === 'success' && (
                                <div className={`vf-alert vf-alert--success ${styles.alert}`}>
                                    <div className="vf-alert__content">
                                        <p>Thank you for your feedback! We have received your submission and will review
                                            it shortly.</p>
                                    </div>
                                </div>
                            )}

                            {submitStatus === 'error' && (
                                <div className={`vf-alert vf-alert--error ${styles.alert}`}>
                                    <div className="vf-alert__content">
                                        <p>Sorry, there was an error submitting your feedback. Please try again or
                                            contact us directly.</p>
                                    </div>
                                </div>
                            )}

                            <form onSubmit={handleSubmit} className={styles.feedbackForm}>
                                <p/>
                                <div className="vf-form__item">
                                    <label htmlFor="name" className="vf-form__label">
                                        Name <span className="vf-form__label__required">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        id="name"
                                        name="name"
                                        value={formData.name}
                                        onChange={handleInputChange}
                                        className="vf-form__input"
                                        placeholder="Enter your name"
                                        required
                                    />
                                </div>
                                <p/>
                                <div className="vf-form__item">
                                    <label htmlFor="email" className="vf-form__label">
                                        Email <span className="vf-form__label__required">*</span>
                                    </label>
                                    <input
                                        type="email"
                                        id="email"
                                        name="email"
                                        value={formData.email}
                                        onChange={handleInputChange}
                                        className="vf-form__input"
                                        placeholder="Enter your email"
                                        required
                                    />
                                </div>
                                <p/>
                                <div className="vf-form__item">
                                    <label htmlFor="cc" className="vf-form__label">
                                        CC (Optional)
                                    </label>
                                    <input
                                        type="text"
                                        id="cc"
                                        name="cc"
                                        value={formData.cc}
                                        onChange={handleInputChange}
                                        className="vf-form__input"
                                        placeholder="Enter CC (Comma separated)"
                                    />
                                    <small className="vf-form__helper">Add additional email addresses separated by
                                        commas</small>
                                </div>
                                <p/>
                                <div className="vf-form__item">
                                    <label htmlFor="subject" className="vf-form__label">
                                        Subject <span className="vf-form__label__required">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        id="subject"
                                        name="subject"
                                        value={formData.subject}
                                        onChange={handleInputChange}
                                        className="vf-form__input"
                                        placeholder="Enter feedback subject"
                                        required
                                    />
                                </div>
                                <p/>
                                <div className="vf-form__item">
                                    <label htmlFor="feedback" className="vf-form__label">
                                        Feedback Details <span className="vf-form__label__required">*</span>
                                    </label>
                                    <textarea
                                        id="feedback"
                                        name="feedback"
                                        value={formData.feedback}
                                        onChange={handleInputChange}
                                        className="vf-form__textarea"
                                        placeholder="Please provide detailed feedback about your experience with the METT Data Portal"
                                        rows={8}
                                        required
                                    />
                                </div>

                                <div className="vf-form__item">
                                    <button
                                        type="submit"
                                        className="vf-button vf-button--primary"
                                        disabled={!isFormValid || isSubmitting}
                                    >
                                        {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>

                    {/*<div className="vf-grid__col--span-1">*/}
                    {/*    <div className="vf-content">*/}
                    {/*        <div className="vf-card">*/}
                    {/*            <div className="vf-card__content">*/}
                    {/*                <h3>How can we help?</h3>*/}
                    {/*                <p>Your feedback helps us improve the METT Data Portal. We welcome:</p>*/}
                    {/*                <ul>*/}
                    {/*                    <li>Bug reports and technical issues</li>*/}
                    {/*                    <li>Feature requests and suggestions</li>*/}
                    {/*                    <li>Data accuracy concerns</li>*/}
                    {/*                    <li>User experience feedback</li>*/}
                    {/*                    <li>General questions about the portal</li>*/}
                    {/*                </ul>*/}
                    {/*                <p>We typically respond within 2-3 business days.</p>*/}
                    {/*            </div>*/}
                    {/*        </div>*/}
                    {/*    </div>*/}
                    {/*</div>*/}
                </div>
            </div>
        </div>
    );
};

export default FeedbackPage; 