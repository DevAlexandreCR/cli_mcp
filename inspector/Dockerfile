# Pin inspector version — update here when upgrading
# @modelcontextprotocol/inspector@0.14.0
FROM node:lts-alpine

WORKDIR /inspector

# Install the pinned version so it's baked into the image (no runtime npx fetch)
RUN npm install -g @modelcontextprotocol/inspector@0.14.0

EXPOSE 6274

CMD ["mcp-inspector", "--port", "6274"]
