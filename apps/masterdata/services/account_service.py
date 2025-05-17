from ..models import Account
from typing import List
import logging

logger = logging.getLogger(__name__)

class AccountService:
    @staticmethod
    def get_all_accounts() -> List[Account]:
        """
        Récupère tous les comptes
        
        Returns:
            List[Account]: Liste des comptes
        """
        try:
            logger.info("Récupération de tous les comptes")
            accounts = Account.objects.all()
            logger.info(f"{accounts.count()} comptes trouvés")
            return accounts
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des comptes: {str(e)}")
            raise 