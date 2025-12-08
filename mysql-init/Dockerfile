FROM mysql:8.0

# Copy SQL files
COPY *.sql /docker-entrypoint-initdb.d/

# Ensure proper permissions
RUN chmod 644 /docker-entrypoint-initdb.d/*.sql
