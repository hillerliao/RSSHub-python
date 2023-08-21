# syntax=docker/dockerfile:1.2
FROM python:3.11-alpine AS build
WORKDIR /app
COPY requirements.txt ./ 
RUN --no-cache pip install -r requirements.txt
COPY . .
RUN pip install gunicorn

FROM python:3.11-alpine AS runtime
WORKDIR /app 
COPY --from=build /app .
USER 1000:1000

EXPOSE 8080  
CMD ["gunicorn", "-w", "4", "-b", ":8080", "app:app"]
