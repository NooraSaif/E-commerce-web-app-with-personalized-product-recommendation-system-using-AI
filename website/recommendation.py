from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from cachetools import TTLCache
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Cache for store similarity matrix (2-minute)
similarity_matrix_cache = TTLCache(maxsize=1, ttl=120)
# Cache for store final result of search operation (2-minute)
recommendation_cache = TTLCache(maxsize=1000, ttl=120)

class PersonalizedRecommendationSystem:
    # Initialize the recommendation system.
    def __init__(self, max_features=500):
        self.max_features = max_features
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.similarity_matrix = None
        self.products = []
        self.product_ids = []
    # Build recommendation model using TF-IDF and cosine similarity
    def build_model(self, products):
        try:
            if not products or len(products) < 2:
                logger.warning("Not enough products to build recommendation model")
                return False         
            self.products = products
            self.product_ids = [p.id for p in products]
            
            # combine product features and Weight them by importance
            product_features = []
            for product in products:
                data = (f"{product.product_name} " * 2 +  # this weighted 2x
                       f"{product.description} " +
                       f"{product.main_category} " +
                       f"{product.sub_category}")
                product_features.append(data)
            
            # Calculate TF-IDF vectors
            self.tfidf_vectorizer = TfidfVectorizer(max_features=self.max_features, stop_words='english',lowercase=True)
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(product_features)
            
            # Calculate cosine similarity matrix
            self.similarity_matrix = cosine_similarity(self.tfidf_matrix)
            
            # Cache the similarity matrix
            similarity_matrix_cache['matrix'] = self.similarity_matrix
            similarity_matrix_cache['product_ids'] = self.product_ids
            similarity_matrix_cache['timestamp'] = datetime.utcnow()
            
            # Clear the results cache since the model has been rebuilt
            recommendation_cache.clear()
            
            logger.info(f"Successfully created an RS model for {len(products)} products")
            return True
            
        except Exception as e:
            logger.error(f"Error creating RS model: {str(e)}")
            return False
    
    # Get similar products for specific product using similarity matrix
    def get_similar_products(self, product_id, top_k=5, exclude_ids=None):
        if exclude_ids is None:
            exclude_ids = []
        
        # Check cache first
        cache_key = f'similar_{product_id}_{top_k}'
        if cache_key in recommendation_cache:
            return recommendation_cache[cache_key]
        
        try:
            if self.similarity_matrix is None or product_id not in self.product_ids:
                return []
            
            product_index = self.product_ids.index(product_id)
            similarity_scores = self.similarity_matrix[product_index]
            
            # create list
            similarity_list = []
            for index, score in enumerate(similarity_scores):
                pid = self.product_ids[index]
                if pid != product_id and pid not in exclude_ids:
                    similarity_list.append((pid, float(score)))
            
            # Sort by similarity score and get top N
            similarity_list.sort(key=lambda x: x[1], reverse=True)
            max_num = max(top_k, 10)
            top_similer_products = similarity_list[:max_num]
            
            # store the result in cache memory
            recommendation_cache[cache_key] = top_similer_products
        
            return top_similer_products
            
        except Exception as e:
            logger.error(f"Error getting similar products for {product_id}: {str(e)}")
            return []
    
    # Get personalized recommendations based on user's interaction history
    def get_personalized_recommendations(self, user, top_k=5):
        try:
            # display new arrival products if no interaction history
            if not hasattr(user, 'interactions') or len(user.interactions) == 0:
                return []
            
            user_product_ids = set()
            interaction_weights = {}
            
            for interaction in user.interactions:
                user_product_ids.add(interaction.product_id)

                weights = {
                    'add_to_cart': 1.5,
                    'view': 1.0
                }

                base_weight = weights.get(interaction.type, 1.0) * max(interaction.weight, 1.0)
                interaction_weights[interaction.product_id] = base_weight
            
            # Find similar products to what user has interacted with
            all_recommendations = {}
            most_similar_products = 20

            for product_id in user_product_ids:
                similarity_list = self.get_similar_products(
                    product_id,
                    top_k=most_similar_products,
                    exclude_ids=list(user_product_ids)
                )

                # Weight by similarity and user's interaction strength
                user_weight = interaction_weights.get(product_id, 1.0)

                for rec_product_id, similarity_score in similarity_list:
                    if rec_product_id not in all_recommendations:
                        all_recommendations[rec_product_id] = 0.0

                    divisor = 10.0
                    combined_score = similarity_score * (user_weight / divisor)
                    all_recommendations[rec_product_id] += combined_score
            
            # Sort by combined score and return top N
            sorted_recommendations = sorted(
                all_recommendations.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # return 10 recommendations
            desired = max(top_k, 10)
            return sorted_recommendations[:desired]
            
        except Exception as e:
            logger.error(f"Error getting personalized recommendations: {str(e)}")
            return []
    
    # Get recommendations filtered by product category for diversity
    def get_category_recommendations(self, product_id, top_k=5):
        try:
            from . import database
            from .models import Product
            
            product = Product.query.get(product_id)
            if not product:
                return []
            
            similarity_list = self.get_similar_products(product_id, top_k=top_k * 2)
            if not similarity_list:
                return []

            rec_ids = [pid for pid, _ in similarity_list]
            products_objs = Product.query.filter(Product.id.in_(rec_ids), Product.in_stock > 0).all()
            
            product_map = {p.id: p for p in products_objs}

            same_category, other_category = [], []
            for rec_id, score in similarity_list:
                rec_product = product_map.get(rec_id)
                if rec_product:
                    if rec_product.main_category == product.main_category:
                        same_category.append((rec_id, score))
                    else:
                        other_category.append((rec_id, score))
            
            # Return mostly same category with some diversity
            result = same_category[:int(top_k * 0.7)]
            result.extend(other_category[:int(top_k * 0.3)])
            
            return result[:top_k]
            
        except Exception as e:
            logger.error(f"Error getting category-aware recommendations: {str(e)}")
            return []


# Global instance
_engine = None

# Initialize the recommendation system on app startup.
def initialize_engine(app):
    global _engine
    try:
        from .models import Product
        
        with app.app_context():
            products = Product.query.filter(Product.in_stock > 0).all()
            
            if not products:
                logger.warning("No products found for RS")
                return False
            
            _engine = PersonalizedRecommendationSystem()
            success = _engine.build_model(products)
            
            if success:
                logger.info("RS initialized successfully")
            else:
                logger.error("Failed to initialize RS model")
            
            return success
    except Exception as e:
        logger.error(f"Error initializing RS: {str(e)}")
        return False

def get_engine():
    global _engine
    if _engine is None:
        logger.warning("Recommendation system not initialized")
    return _engine

def rebuild_recommendations(app):
    global _engine
    return initialize_engine(app)
