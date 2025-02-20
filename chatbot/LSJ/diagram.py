from diagrams import Diagram, Cluster
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.storage import S3
from diagrams.onprem.client import User
from diagrams.onprem.compute import Server

with Diagram("AWS Architecture", show=False, filename="aws_architecture"):
    user = User("User")
    
    with Cluster("Frontend"):
        react = Server("React App")
    
    with Cluster("Backend"):
        django = Server("Django API")
        db = RDS("Database")
    
    with Cluster("AWS Cloud"):
        ec2 = EC2("EC2 Instance")
        # storage = S3("S3 Bucket")
    
    # 사용자 흐름
    user >> react >> django >> db
    django >> ec2
