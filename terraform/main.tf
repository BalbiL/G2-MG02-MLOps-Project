provider "aws" {
  region = "eu-west-3"
}

# --- 1. RÉCUPÉRATION DES RESSOURCES EXISTANTES ---

data "aws_iam_role" "execution_role" {
  name = "ecsTaskExecutionRole"
}

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

# --- 4. SÉCURITÉ (Security Groups) ---

# Groupe de sécurité pour l'ALB (Lui doit être accessible sur le port 80 public)
resource "aws_security_group" "alb_sg" {
  name        = "g2-mg02-alb-sg"
  description = "Security Group for Application Load Balancer"
  vpc_id      = data.aws_vpc.default.id

  # Entrée : HTTP (80) ouvert à tous
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Sortie : Tout autorisé (pour parler aux conteneurs)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Groupe de sécurité pour les Conteneurs ECS
resource "aws_security_group" "app_sg" {
  name        = "g2-mg02-news-reco-sg-tf"
  description = "Security Group managed by Terraform for ECS"
  vpc_id      = data.aws_vpc.default.id

  # Autoriser Streamlit (8501) 
  # (Idéalement on restreindrait à "security_groups = [aws_security_group.alb_sg.id]", 
  # mais pour le debug on laisse 0.0.0.0/0)
  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Autoriser l'API (8000)
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- [NOUVEAU] 5. LOAD BALANCER (ALB) ---

resource "aws_lb" "main" {
  name               = "g2-mg02-news-reco-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [
      "subnet-03ac2adb51071d022",
      "subnet-04274dee3c914f032",
      "subnet-04ac053b02c2936d8"
  ]
}

resource "aws_lb_target_group" "front_tg" {
  name        = "g2-mg02-front-tg"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip" # OBLIGATOIRE pour Fargate

  health_check {
    path                = "/"    # Streamlit répond sur la racine
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
}

resource "aws_lb_listener" "front_listener" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.front_tg.arn
  }
}

# --- 6. TASK DEFINITION ---
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
      
     
      environment = [
        { name = "SUPABASE_URL", value = var.supabase_url },
        { name = "SUPABASE_KEY", value = var.supabase_key }
      ]

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
        { name = "SUPABASE_URL", value = var.supabase_url},
        { name = "SUPABASE_KEY", value = var.supabase_key }
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

# --- 7. SERVICE ECS (Mis à jour) ---
resource "aws_ecs_service" "app_service" {
  name            = "g2-mg02-news-reco-task-service-nyvdt5tq"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  # [NOUVEAU] Connexion au Load Balancer
  load_balancer {
    target_group_arn = aws_lb_target_group.front_tg.arn
    container_name   = "g2-mg02-frontend-container"
    container_port   = 8501
  }

  network_configuration {
    subnets = [
      "subnet-03ac2adb51071d022",
      "subnet-04274dee3c914f032",
      "subnet-04ac053b02c2936d8"
    ]
    security_groups  = [aws_security_group.app_sg.id]
    assign_public_ip = true
  }

  depends_on = [aws_lb_listener.front_listener]
}

# --- 8. OUTPUTS ---
output "alb_url" {
  value = aws_lb.main.dns_name
  description = "L'URL fixe de votre application"
}