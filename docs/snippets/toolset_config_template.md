## Configuration

=== "Mavrick CLI"

    Add the following to **~/.mavrick/config.yaml**. Create the file if it doesn't exist:

    ```yaml
    toolsets:
        TOOLSET_PATH:
            enabled: true
            config:
                # Add your configuration here
                CUSTOM_CONFIG
    ```

=== "Robusta Helm Chart"

    ```yaml
    mavrick:
        toolsets:
            TOOLSET_PATH:
                enabled: true
                config:
                    # Add your configuration here
                    CUSTOM_CONFIG
    ```
