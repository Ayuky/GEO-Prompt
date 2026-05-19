# ============================================================
# Stage 1: Maven 编译
# ============================================================
FROM maven:3-eclipse-temurin-17 AS builder

WORKDIR /build

# 先复制 pom 文件，利用 Docker 缓存层加速构建
COPY pom.xml .
COPY ruoyi-admin/pom.xml ruoyi-admin/
COPY ruoyi-framework/pom.xml ruoyi-framework/
COPY ruoyi-system/pom.xml ruoyi-system/
COPY ruoyi-quartz/pom.xml ruoyi-quartz/
COPY ruoyi-generator/pom.xml ruoyi-generator/
COPY ruoyi-common/pom.xml ruoyi-common/

# 下载依赖（这一步会被缓存，除非 pom 变化）
RUN mvn dependency:go-offline -B -q

# 复制源码
COPY . .

# 编译打包（跳过测试，加速构建）
RUN mvn package -DskipTests -B -q

# ============================================================
# Stage 2: 运行镜像
# ============================================================
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# 设置时区
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

# 从构建阶段复制 jar
COPY --from=builder /build/ruoyi-admin/target/*.jar app.jar

# 创建文件上传目录
RUN mkdir -p /home/ruoyi/uploadPath

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
