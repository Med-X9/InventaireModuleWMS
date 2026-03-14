"""
Exceptions personnalisées pour la génération de PDF
"""


class PDFGenerationError(Exception):
    """Exception de base pour les erreurs de génération PDF"""
    pass


class PDFValidationError(PDFGenerationError):
    """Exception levée lors d'une erreur de validation des données pour la génération PDF"""
    pass


class PDFNotFoundError(PDFGenerationError):
    """Exception levée lorsqu'une ressource requise pour la génération PDF n'est pas trouvée"""
    pass


class PDFEmptyContentError(PDFGenerationError):
    """Exception levée lorsque le PDF généré est vide (aucun contenu à exporter)"""
    pass


class PDFInvalidContentError(PDFGenerationError):
    """Exception levée lorsque le contenu du PDF généré est invalide"""
    pass


class PDFRepositoryError(PDFGenerationError):
    """Exception levée lors d'une erreur dans le repository PDF"""
    pass


class PDFServiceError(PDFGenerationError):
    """Exception levée lors d'une erreur dans le service PDF"""
    pass

