#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from apps.inventory.models import Job, JobDetail
from apps.masterdata.models import Location

def check_job_data():
    # Vérifier le job avec l'ID 17
    job = Job.objects.get(id=17)
    print(f"Job ID: {job.id}")
    print(f"Job Reference: {job.reference}")
    print(f"Job Status: {job.status}")
    print(f"Job Warehouse: {job.warehouse}")
    print(f"Job Inventory: {job.inventory}")
    
    # Vérifier les JobDetail associés
    job_details = JobDetail.objects.filter(job=job)
    print(f"\nNombre de JobDetail pour ce job: {job_details.count()}")
    
    if job_details.exists():
        print("\nJobDetail trouvés:")
        for detail in job_details:
            print(f"  - ID: {detail.id}, Reference: {detail.reference}, Location: {detail.location}, Status: {detail.status}")
    else:
        print("\nAucun JobDetail trouvé pour ce job")
        
        # Vérifier s'il y a des locations disponibles
        locations = Location.objects.all()
        print(f"\nNombre total de locations dans la base: {locations.count()}")
        if locations.exists():
            print("Premières 5 locations:")
            for loc in locations[:5]:
                print(f"  - ID: {loc.id}, Reference: {loc.location_reference}")

if __name__ == "__main__":
    check_job_data() 