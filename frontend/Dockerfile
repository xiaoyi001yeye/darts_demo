# 使用官方 Nginx 镜像作为前端服务器
FROM nginx:alpine

# 复制前端静态文件到 Nginx 默认目录
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/
COPY index.html /usr/share/nginx/html/

# 复制自定义 nginx 配置，并移除默认配置
COPY nginx.conf /etc/nginx/nginx.conf
RUN rm -f /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80