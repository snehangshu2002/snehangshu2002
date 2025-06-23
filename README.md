<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snehangshu Bhuin - GitHub Profile</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        .animate-fadeInUp {
            animation: fadeInUp 1s ease-out forwards;
        }
        .animate-pulse {
            animation: pulse 2s infinite;
        }
        .section-hidden {
            opacity: 0;
            transform: translateY(20px);
        }
    </style>
</head>
<body class="bg-gray-900 text-white font-sans">
    <div class="container mx-auto px-4 py-10">
        <!-- Header Section -->
        <header class="text-center mb-12 animate-fadeInUp">
            <img src="https://avatars.githubusercontent.com/u/your-github-id" alt="Profile Picture" class="w-32 h-32 rounded-full mx-auto mb-4 border-4 border-blue-500 animate-pulse">
            <h1 class="text-4xl font-bold text-blue-400">Snehangshu Bhuin</h1>

            <p class="text-xl text-gray-300">Statistics Postgraduate | Data Scientist | Machine Learning Enthusiast</p>
            <div class="flex justify-center gap-4 mt-4">
                <a href="mailto:snehangshubhuin@gmail.com" class="text-blue-400 hover:text-blue-600"><i class="fas fa-envelope"></i></a>
                <a href="https://www.linkedin.com/in/snehangshu-bhuin-b02987279" class="text-blue-400 hover:text-blue-600"><i class="fab fa-linkedin"></i></a>
                <a href="https://github.com/snehangshu2002" class="text-blue-400 hover:text-blue-600"><i class="fab fa-github"></i></a>
            </div>
        </header>

        <!-- Summary Section -->
        <section class="mb-12 section-hidden">
            <h2 class="text-3xl font-semibold text-blue-400 mb-4">About Me</h2>
            <p class="text-gray-300 leading-relaxed">
                Motivated and detail-oriented statistics postgraduate student with hands-on experience in machine learning, data analysis, and visualization. Skilled in Python, R, and SQL, with a solid understanding of statistical modeling, time series analysis, and natural language processing. Developed multiple end-to-end data science projects including fake news detection and heart disease prediction using real-world datasets. Proficient in creating interactive dashboards using Streamlit and presenting data-driven insights. Passionate about solving complex problems through data and continuously expanding knowledge in AI and analytics.
            </p>
        </section>

        <!-- Education Section -->
        <section class="mb-12 section-hidden">
            <h2 class="text-3xl font-semibold text-blue-400 mb-4">Education</h2>
            <div class="bg-gray-800 p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow">
                <h3 class="text-xl font-bold">M.Sc. in Statistics</h3>
                <p class="text-gray-400">Visva-Bharati University | 2023 - 2025</p>
                <p class="text-gray-300">Courses: Machine Learning, Time Series Analysis, Data Mining, Advanced Statistics</p>
            </div>
            <div class="bg-gray-800 p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow mt-4">
                <h3 class="text-xl font-bold">B.Sc. in Statistics</h3>
                <p class="text-gray-400">Visva-Bharati University | 2020 - 2023</p>
                <p class="text-gray-300">Courses: Probability, Regression Analysis</p>
            </div>
        </section>

        <!-- Skills Section -->
        <section class="mb-12 section-hidden">
            <h2 class="text-3xl font-semibold text-blue-400 mb-4">Skills</h2>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="bg-gray-800 p-4 rounded-lg text-center hover:bg-blue-700 transition-colors">
                    <h3 class="font-bold">Programming</h3>
                    <p>Python, R, SQL</p>
                </div>
                <div class="bg-gray-800 p-4 rounded-lg text-center hover:bg-blue-700 transition-colors">
                    <h3 class="font-bold">Data Science</h3>
                    <p>Machine Learning, NLP, Data Analysis, Visualization</p>
                </div>
                <div class="bg-gray-800 p-4 rounded-lg text-center hover:bg-blue-700 transition-colors">
                    <h3 class="font-bold">Tools</h3>
                    <p>Excel, Streamlit, Tableau, LaTeX</p>
                </div>
            </div>
        </section>

        <!-- Projects Section -->
        <section class="mb-12 section-hidden">
            <h2 class="text-3xl font-semibold text-blue-400 mb-4">Projects</h2>
            <div class="space-y-6">
                <div class="bg-gray-800 p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow">
                    <h3 class="text-xl font-bold">Fake News Classifier</h3>
                    <p class="text-gray-400">2024 | <a href="https://github.com/snehangshu2002/Data-Science-Project" class="text-blue-400 hover:underline">GitHub</a></p>
                    <p class="text-gray-300">Created a Python tool with NLP and Streamlit to sort fake from real news, hitting 90% accuracy on a dataset of 5,000+ articles.</p>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow">
                    <h3 class="text-xl font-bold">Heart Disease Prediction</h3>
                    <p class="text-gray-400">2023 | <a href="https://github.com/snehangshu2002/Heart-Disease-Classification" class="text-blue-400 hover:underline">GitHub</a></p>
                    <p class="text-gray-300">Built a Python model using logistic regression and decision trees, predicting heart disease with 85% accuracy across 1,500+ patient records.</p>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow">
                    <h3 class="text-xl font-bold">WhatsApp Chat Analyzer</h3>
                    <p class="text-gray-400">2024 | <a href="https://whatsapp-chat-analysis-2002.streamlit.app/" class="text-blue-400 hover:underline">Live App</a> | <a href="https://github.com/snehangshu2002/whatsapp-chat-analysis" class="text-blue-400 hover:underline">GitHub</a></p>
                    <p class="text-gray-300">Developed an interactive dashboard using Python, Streamlit, NLTK, and Plotly to analyze exported WhatsApp chats with message stats, emoji usage, and sentiment trends.</p>
                </div>
                <div class="bg-gray-800 p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow">
                    <h3 class="text-xl font-bold">Movie Recommendation System</h3>
                    <p class="text-gray-400">2024 | <a href="https://movie-recommendation2002.streamlit.app/" class="text-blue-400 hover:underline">Live App</a> | <a href="https://github.com/snehangshu2002/Movie-Recommendation" class="text-blue-400 hover:underline">GitHub</a></p>
                    <p class="text-gray-300">Built a content-based movie recommender using Python, TMDB API, and NLP with cosine similarity, displaying movies with posters and trailers.</p>
                </div>
            </div>
        </section>

        <!-- Virtual Experience Section -->
        <section class="mb-12 section-hidden">
            <h2 class="text-3xl font-semibold text-blue-400 mb-4">Virtual Experience</h2>
            <div class="bg-gray-800 p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow">
                <h3 class="text-xl font-bold">Deloitte Australia Data Analytics Job Simulation</h3>
                <p class="text-gray-400">Forage | June 2025 | <a href="https://forage-uploads-prod.s3.amazonaws.com/completion-certificates/9PBTqmSxAf6zZTseP/io9DzWKe3PTsiS6GG_9PBTqmSxAf6zZTseP_k6g6cv8LxzapAyEdB_1750658504746_completion_certificate.pdf" class="text-blue-400 hover:underline">Certificate</a></p>
                <p class="text-gray-300">Completed a simulation involving data analysis and forensic technology, creating an interactive Tableau dashboard and using Excel for insights.</p>
            </div>
        </section>

        <!-- Certifications Section -->
        <section class="mb-12 section-hidden">
            <h2 class="text-3xl font-semibold text-blue-400 mb-4">Certifications</h2>
            <div class="bg-gray-800 p-6 rounded-lg shadow-lg hover:shadow-xl transition-shadow">
                <h3 class="text-xl font-bold">Data Science Certification</h3>
                <p class="text-gray-400">DataSpace Academy | 2024 | <a href="https://drive.google.com/file/d/1gKpt4Jj2LKN5X2iF4THYTr2kX-cGBP4q/view" class="text-blue-400 hover:underline">Certificate</a></p>
            </div>
        </section>
    </div>

    <script>
        // Intersection Observer for animations
        const sections = document.querySelectorAll('.section-hidden');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.remove('section-hidden');
                    entry.target.classList.add('animate-fadeInUp');
                }
            });
        }, { threshold: 0.1 });

        sections.forEach(section => observer.observe(section));
    </script>
</body>
</html>
