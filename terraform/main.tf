provider "aws" {
  region = "eu-west-3"
}

# --- 1. RÉCUPÉRATION DES RESSOURCES EXISTANTES ---

# On récupère le rôle IAM existant (celui mentionné dans votre JSON)
data "aws_iam_role" "execution_role" {
  name = "ecsTaskExecutionRole"
}

# [NOUVEAU] On récupère le VPC par défaut pour y créer le Security Group
data "aws_vpc" "default" {
  default = true
}

# --- 2. CLUSTER ECS ---
resource "aws_ecs_cluster" "main" {
  name = "g2-mg02-news-reco-cluster"
}

# --- 3. GESTION DES LOGS (CloudWatch) ---
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/g2-mg02-news-reco-task"
  retention_in_days = 1
}

# --- [NOUVEAU] 4. SECURITY GROUP (Pare-feu) ---
# Terraform va créer ce groupe de sécurité automatiquement
resource "aws_security_group" "app_sg" {
  name        = "g2-mg02-news-reco-sg-tf"
  description = "Security Group managed by Terraform for ECS"
  vpc_id      = data.aws_vpc.default.id

  # Autoriser Streamlit (8501) depuis partout
  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Autoriser l'API (8000) depuis partout
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Règle de sortie (Egress) : Indispensable pour télécharger les images Docker !
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- 5. TASK DEFINITION (Le plan des conteneurs) ---
resource "aws_ecs_task_definition" "app" {
  family                   = "g2-mg02-news-reco-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 1024 # 1 vCPU
  memory                   = 5120 # 5 GB
  
  execution_role_arn       = data.aws_iam_role.execution_role.arn
  task_role_arn            = data.aws_iam_role.execution_role.arn

  container_definitions = jsonencode([
    # --- CONTENEUR ML ---
    {
      name      = "g2-mg02-ml-container"
      image     = "073184925698.dkr.ecr.eu-west-3.amazonaws.com/g2-mg02-news-reco-ml:latest"
      essential = true
      portMappings = [{ containerPort = 9000, hostPort = 9000, protocol = "tcp" }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region"        = "eu-west-3"
          "awslogs-stream-prefix" = "ecs"
          "awslogs-create-group"  = "true"
        }
      }
    },

    # --- CONTENEUR API ---
    {
      name      = "g2-mg02-api-container"
      image     = "073184925698.dkr.ecr.eu-west-3.amazonaws.com/g2-mg02-news-reco-api:latest"
      essential = true
      portMappings = [{ containerPort = 8000, hostPort = 8000, protocol = "tcp" }]
      environment = [
        { name = "MODEL_HOST", value = "localhost" },
        { name = "MODEL_PORT", value = "9000" },
        { name = "SUPABASE_URL", value = "https://fnjaisjmtykolnojtafy.supabase.co" },
        { name = "SUPABASE_KEY", value = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZuamFpc2ptdHlrb2xub2p0YWZ5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzIyNDUyOSwiZXhwIjoyMDc4ODAwNTI5fQ.uPTugqsELADLJvZ0dHaUrhvS2SK48FJJxBlgsJ8_9qo" }
      ]
      dependsOn = [{ containerName = "g2-mg02-ml-container", condition = "START" }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region"        = "eu-west-3"
          "awslogs-stream-prefix" = "ecs"
          "awslogs-create-group"  = "true"
        }
      }
    },

    # --- CONTENEUR FRONTEND ---
    {
      name      = "g2-mg02-frontend-container"
      image     = "073184925698.dkr.ecr.eu-west-3.amazonaws.com/g2-mg02-news-reco-frontend:latest"
      essential = true
      portMappings = [{ containerPort = 8501, hostPort = 8501, protocol = "tcp" }]
      environment = [
        { name = "API_HOST", value = "localhost" },
        { name = "API_PORT", value = "8000" },
        { name = "MODEL_HOST", value = "localhost" },
        { name = "MODEL_PORT", value = "9000" }
      ]
      dependsOn = [{ containerName = "g2-mg02-api-container", condition = "START" }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_logs.name
          "awslogs-region"        = "eu-west-3"
          "awslogs-stream-prefix" = "ecs"
          "awslogs-create-group"  = "true"
        }
      }
    }
  ])
}

# --- 6. SERVICE ECS (Le déploiement) ---
resource "aws_ecs_service" "app_service" {
  name            = "g2-mg02-news-reco-task-service-nyvdt5tq"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    # Vos sous-réseaux (conservés tels quels)
    subnets = [
      "subnet-03ac2adb51071d022",
      "subnet-04274dee3c914f032",
      "subnet-04ac053b02c2936d8"
    ]
    
    # [CORRECTION] On utilise l'ID du security group créé par Terraform
    security_groups  = [aws_security_group.app_sg.id]
    
    assign_public_ip = true
  }
}