# Baseten

Configure MavrickGPT to use [Baseten Model APIs](https://docs.baseten.co/inference/model-apis/overview){:target="_blank"} for hosted open-weight models such as Kimi K3 and GLM 5.3.

## Configuration

Use LiteLLM's native `baseten/` prefix with the Baseten model slug (`baseten/<organization>/<model>`). Only `BASETEN_API_KEY` is required: LiteLLM fills in the `https://inference.baseten.co/v1` endpoint itself.

!!! warning "Do not use the `openai/` prefix"
    Baseten's endpoint is OpenAI-compatible, so `model: openai/zai-org/GLM-5.3` with `api_base: https://inference.baseten.co/v1` also answers requests. But MavrickGPT then cannot find the model in LiteLLM's registry: the registry keys Baseten models as `baseten/<slug>`, and an `openai/` model is looked up as `openai/<slug>` and `<slug>`. MavrickGPT falls back to a 200K context window, a 64K output budget and zero cost per token, which do not match the model.

=== "Mavrick CLI"

    ```bash
    export BASETEN_API_KEY="..."
    mavrick ask "what pods are failing?" --model="baseten/zai-org/GLM-5.3"
    ```

=== "Mavrick Helm Chart"

    Create a Kubernetes secret in the namespace Mavrick runs in:

    ```bash
    kubectl create secret generic mavrick-baseten \
      --from-file=BASETEN_API_KEY=/path/to/baseten-api-key \
      -n <namespace>
    ```

    When using the **standalone Mavrick Helm Chart**, update your `values.yaml`:

    ```yaml
    extraEnvVarsSecrets:
      - mavrick-baseten

    additionalEnvVars:
      - name: MODEL
        value: "glm-5-3"  # modelList key name

    modelList:
      glm-5-3:
        model: baseten/zai-org/GLM-5.3
      kimi-k3:
        model: baseten/moonshotai/Kimi-K3
        # Kimi K3 is not in LiteLLM's registry yet; see "Models missing from LiteLLM" below.
        input_cost_per_token: 0.000003
        output_cost_per_token: 0.000015
        custom_args:
          max_context_size: 1048576
    ```

    Apply the configuration:

    ```bash
    helm upgrade mavrick robusta/mavrick -f values.yaml
    ```

=== "Robusta Helm Chart"

    Create a Kubernetes secret in the namespace Mavrick runs in:

    ```bash
    kubectl create secret generic mavrick-baseten \
      --from-file=BASETEN_API_KEY=/path/to/baseten-api-key \
      -n <namespace>
    ```

    When using the **Robusta Helm Chart** (which includes MavrickGPT), update your `generated_values.yaml`:

    ```yaml
    mavrick:
      extraEnvVarsSecrets:
        - mavrick-baseten

      additionalEnvVars:
        - name: MODEL
          value: "glm-5-3"  # modelList key name

      modelList:
        glm-5-3:
          model: baseten/zai-org/GLM-5.3
        kimi-k3:
          model: baseten/moonshotai/Kimi-K3
          # Kimi K3 is not in LiteLLM's registry yet; see "Models missing from LiteLLM" below.
          input_cost_per_token: 0.000003
          output_cost_per_token: 0.000015
          custom_args:
            max_context_size: 1048576
    ```

    Apply the configuration:

    ```bash
    helm upgrade robusta robusta/robusta -f generated_values.yaml --set clusterName=<YOUR_CLUSTER_NAME>
    ```

## Models missing from LiteLLM

LiteLLM's registry covers only some Baseten models, and most of its Baseten entries carry pricing but no context window. MavrickGPT downloads the registry from GitHub at startup, so it sees entries added after the bundled LiteLLM release; `baseten/zai-org/GLM-5.3` is one of those. When MavrickGPT falls back to the bundled copy (GitHub unreachable and no [`LITELLM_MODEL_COST_MAP_URL`](../reference/environment-variables.md#litellm_model_cost_map_url) mirror, or `LITELLM_LOCAL_MODEL_COST_MAP=true`), GLM-5.3 needs the overrides below as well. When MavrickGPT logs `Couldn't find model ... in litellm's model list` or `has no entry in litellm's cost map`, set the values on the model's `modelList` entry:

- `custom_args.max_context_size`: the model's context window, in tokens.
- `input_cost_per_token` and `output_cost_per_token`: USD per token. Both must be set.

Take the numbers from Baseten's model catalog, which reports `context_length`, `max_completion_tokens` and `pricing` per model:

```bash
curl -s https://inference.baseten.co/v1/models \
  -H "Authorization: Bearer $BASETEN_API_KEY" | jq '.data[] | {id, context_length, max_completion_tokens, pricing}'
```
