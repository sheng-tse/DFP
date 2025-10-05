import pandas as pd
import plotly.express as px

class CompensationHeatmap:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.df = None
        self.state_df = None

    def load_data(self):
        """Load and preprocess CSV"""
        self.df = pd.read_csv(self.csv_path)

        # Extract state codes from detailed_location (e.g., "New York, NY" -> "NY")
        self.df["state_code"] = self.df["detailed_location"].str.extract(r",\s*([A-Z]{2})")

        # Aggregate by state
        self.state_df = self.df.groupby("state_code", as_index=False).agg({
            "region_id": "first",
            "region_name": "first",
            "detailed_location": "first",
            "rank": "min",
            "p10": "mean",
            "p25": "mean",
            "p50": "mean",
            "p75": "mean",
            "p90": "mean",
            "normalizedMedian": "mean",
            "url": "first"
        })

    def plot(self, color_col="normalizedMedian", color_scale="Viridis"):
        """Generate and show choropleth map"""
        if self.state_df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        fig = px.choropleth(
            self.state_df,
            locations="state_code",           
            locationmode="USA-states",        
            color=color_col,         
            hover_name="region_name",         
            hover_data={
                "state_code": True,
                "region_id": True,
                "detailed_location": True,
                "rank": True,
                "p10": True,
                "p25": True,
                "p50": True,
                "p75": True,
                "p90": True,
                "normalizedMedian": True,
                "url": True
            },
            color_continuous_scale=color_scale
        )

        fig.update_layout(
            title="Software Engineer Compensation Heatmap by State",
            geo_scope="usa"
        )

        fig.show()


# Example usage
if __name__ == "__main__":
    heatmap = CompensationHeatmap("regions.csv")
    heatmap.load_data()
    heatmap.plot()
