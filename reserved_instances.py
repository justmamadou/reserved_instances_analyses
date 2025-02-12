import boto3
from datetime import datetime, timedelta
import pandas as pd

def analyze_ri_usage():
    """
    Analyse l'utilisation des Reserved Instances et identifie les instances correspondantes
    """
    ec2 = boto3.client('ec2')
    ce = boto3.client('ce')

    # Récupérer les Reserved Instances actives
    ri_response = ec2.describe_reserved_instances(
        Filters=[{'Name': 'state', 'Values': ['active']}]
    )

    # Récupérer toutes les instances en cours d'exécution
    instances_response = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )

    # Préparer les données pour l'analyse
    ri_data = []
    for ri in ri_response['ReservedInstances']:
        ri_info = {
            'ReservationId': ri['ReservedInstancesId'],
            'InstanceType': ri['InstanceType'],
            'AvailabilityZone': ri.get('AvailabilityZone', 'All'),
            'InstanceCount': ri['InstanceCount'],
            'Platform': ri.get('ProductDescription', 'Linux/UNIX')
        }
        ri_data.append(ri_info)

    # Analyser les instances en cours d'exécution
    matching_instances = []
    for reservation in instances_response['Reservations']:
        for instance in reservation['Instances']:
            instance_info = {
                'InstanceId': instance['InstanceId'],
                'InstanceType': instance['InstanceType'],
                'AvailabilityZone': instance['Placement']['AvailabilityZone'],
                'Platform': 'Windows' if 'Platform' in instance else 'Linux/UNIX',
                'Tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
            }
            
            # Vérifier si l'instance correspond à une RI
            for ri in ri_data:
                if (instance_info['InstanceType'] == ri['InstanceType'] and
                    (ri['AvailabilityZone'] == 'All' or 
                     instance_info['AvailabilityZone'] == ri['AvailabilityZone']) and
                    instance_info['Platform'] == ri['Platform']):
                    instance_info['MatchingRI'] = ri['ReservationId']
                    matching_instances.append(instance_info)
                    break

    return pd.DataFrame(matching_instances)

def print_ri_analysis():
    df = analyze_ri_usage()
    print("\nAnalyse des Reserved Instances:")
    print("-" * 50)
    print(f"Total des instances correspondant aux RI: {len(df)}")
    print("\nRépartition par type d'instance:")
    print(df['InstanceType'].value_counts())
    print("\nRépartition par zone de disponibilité:")
    print(df['AvailabilityZone'].value_counts())
    
    # Exporter en CSV pour une analyse plus détaillée
    df.to_csv('ri_analysis.csv', index=False)
    print("\nRapport détaillé exporté dans 'ri_analysis.csv'")

if __name__ == "__main__":
    print_ri_analysis()
